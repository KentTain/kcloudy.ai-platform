"""
角色管理服务

提供角色 CRUD 和权限分配功能。
"""

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.audit.decorator import audit_log
from framework.audit.utils import get_model_before_data
from iam.models import Permission, Role, RolePermission, UserRole
from iam.services.permission_service import PermissionCheckService

_logger = logger.bind(name=__name__)


class RoleService:
    """角色管理服务"""

    @staticmethod
    @audit_log(
        module="iam",
        resource="role",
        action="create",
        resource_id_getter=lambda result: result.id,
        resource_name_getter=lambda result: result.name,
    )
    async def create(
        session: AsyncSession,
        code: str,
        name: str,
        tenant_id: str | None = None,
        description: str | None = None,
        is_system: bool = False,
    ) -> Role:
        """
        创建角色

        Args:
            session: 数据库会话
            code: 角色编码
            name: 角色名称
            tenant_id: 租户 ID（None 为全局角色）
            description: 描述
            is_system: 是否系统内置

        Returns:
            Role
        """
        # 检查编码是否已存在（同租户内）
        stmt = select(Role).where(Role.code == code)
        if tenant_id:
            stmt = stmt.where(Role.tenant_id == tenant_id)
        else:
            stmt = stmt.where(Role.tenant_id.is_(None))

        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("角色编码已存在")

        role = Role(
            code=code,
            name=name,
            tenant_id=tenant_id,
            description=description,
            is_system=is_system,
        )
        session.add(role)
        await session.flush()
        await session.refresh(role)

        _logger.info(f"创建角色: {code}")
        return role

    @staticmethod
    async def get_by_id(session: AsyncSession, role_id: str) -> Role | None:
        """根据 ID 获取角色"""
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    @audit_log(
        module="iam",
        resource="role",
        action="update",
        resource_id_getter=lambda result: result.id,
        resource_name_getter=lambda result: result.name,
        before_data_getter=lambda args, kwargs: get_model_before_data(
            args, kwargs, model_class=Role, id_param="role_id"
        ),
    )
    async def update(
        session: AsyncSession,
        role_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> Role:
        """更新角色"""
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise ValueError("角色不存在")

        if role.is_system:
            raise ValueError("系统内置角色禁止修改")

        if name is not None:
            role.name = name
        if description is not None:
            role.description = description

        await session.flush()
        await session.refresh(role)

        _logger.info(f"更新角色: {role_id}")
        return role

    @staticmethod
    @audit_log(
        module="iam",
        resource="role",
        action="delete",
        before_data_getter=lambda args, kwargs: get_model_before_data(
            args, kwargs, model_class=Role, id_param="role_id"
        ),
    )
    async def delete(session: AsyncSession, role_id: str) -> bool:
        """删除角色"""
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            return False

        if role.is_system:
            raise ValueError("系统内置角色禁止修改")

        await session.delete(role)
        await session.flush()

        _logger.info(f"删除角色: {role_id}")
        return True

    @staticmethod
    async def list_roles(
        session: AsyncSession,
        tenant_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Role], int]:
        """获取角色列表"""
        # 查询条件
        conditions = []
        if tenant_id:
            # 包含全局角色和租户角色
            conditions.append(
                (Role.tenant_id == tenant_id) | (Role.tenant_id.is_(None))
            )

        # 查询总数
        count_stmt = select(func.count(Role.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = select(Role)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(Role.created_at.desc()).offset(offset).limit(page_size)

        result = await session.execute(stmt)
        roles = list(result.scalars().all())

        return roles, total

    @staticmethod
    async def assign_permissions(
        session: AsyncSession, role_id: str, permission_ids: list[str]
    ) -> None:
        """
        为角色分配权限

        自动从角色推导 tenant_id 用于关联表。

        Args:
            session: 数据库会话
            role_id: 角色 ID
            permission_ids: 权限 ID 列表
        """
        # 获取角色的 tenant_id
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            raise ValueError("角色不存在")

        if role.is_system:
            raise ValueError("系统内置角色禁止修改")

        # 使用角色的 tenant_id（全局角色则 tenant_id 为 None）
        actual_tenant_id = role.tenant_id

        # 删除现有权限
        stmt = select(RolePermission).where(RolePermission.role_id == role_id)
        result = await session.execute(stmt)
        for rp in result.scalars().all():
            await session.delete(rp)

        # 添加新权限
        for perm_id in permission_ids:
            rp = RolePermission(
                role_id=role_id,
                permission_id=perm_id,
                tenant_id=actual_tenant_id,
            )
            session.add(rp)

        await session.flush()
        _logger.info(f"角色分配权限: {role_id} -> {len(permission_ids)} permissions")

        # 触发权限缓存失效
        if actual_tenant_id:
            await PermissionCheckService.invalidate_tenant_permission_cache(
                session, actual_tenant_id
            )

    @staticmethod
    async def get_role_permissions(
        session: AsyncSession, role_id: str
    ) -> list[Permission]:
        """获取角色的权限列表"""
        stmt = (
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == role_id)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


class UserRoleService:
    """用户-角色关联服务"""

    @staticmethod
    async def assign_roles(
        session: AsyncSession, user_id: str, role_ids: list[str]
    ) -> None:
        """
        为用户分配角色

        自动从用户推导 tenant_id 用于关联表。

        Args:
            session: 数据库会话
            user_id: 用户 ID
            role_ids: 角色 ID 列表
        """
        # 获取用户的 tenant_id
        from iam.models import User

        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("用户不存在")

        # 使用用户的 tenant_id
        tenant_id = user.tenant_id

        # 删除现有角色
        stmt = select(UserRole).where(UserRole.user_id == user_id)
        result = await session.execute(stmt)
        for ur in result.scalars().all():
            await session.delete(ur)

        # 添加新角色
        for role_id in role_ids:
            ur = UserRole(user_id=user_id, role_id=role_id, tenant_id=tenant_id)
            session.add(ur)

        await session.flush()
        _logger.info(f"用户分配角色: {user_id} -> {len(role_ids)} roles")

        # 触发权限缓存失效
        await PermissionCheckService.invalidate_user_permission_cache(user_id)

    @staticmethod
    async def get_user_roles(session: AsyncSession, user_id: str) -> list[Role]:
        """获取用户的角色列表"""
        stmt = (
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def remove_role(session: AsyncSession, user_id: str, role_id: str) -> bool:
        """移除用户的某个角色"""
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        result = await session.execute(stmt)
        ur = result.scalar_one_or_none()

        if ur:
            await session.delete(ur)
            await session.flush()
            return True
        return False

    @staticmethod
    async def get_role_options(
        session: AsyncSession, tenant_id: str | None = None
    ) -> list[Role]:
        """
        获取角色选项列表（不分页）

        Args:
            session: 数据库会话
            tenant_id: 租户 ID（None 时获取全局角色）

        Returns:
            list[Role]
        """
        stmt = select(Role)
        if tenant_id:
            stmt = stmt.where(
                (Role.tenant_id == tenant_id) | (Role.tenant_id.is_(None))
            )
        else:
            stmt = stmt.where(Role.tenant_id.is_(None))
        stmt = stmt.order_by(Role.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())


class RoleMemberService:
    """角色成员管理服务"""

    @staticmethod
    async def get_role_members(session: AsyncSession, role_id: str) -> list[dict]:
        """
        获取角色成员列表

        Args:
            session: 数据库会话
            role_id: 角色 ID

        Returns:
            list[dict]: 成员信息列表
        """
        from iam.models import User

        stmt = (
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .where(UserRole.role_id == role_id)
            .order_by(User.username)
        )
        result = await session.execute(stmt)
        users = list(result.scalars().all())

        return [
            {
                "user_id": u.id,
                "username": u.username,
                "nickname": u.nickname,
                "email": u.email,
                "phone": u.phone,
                "status": u.status,
            }
            for u in users
        ]

    @staticmethod
    async def add_role_members(
        session: AsyncSession, role_id: str, user_ids: list[str]
    ) -> int:
        """
        为角色批量添加成员（追加模式）

        Args:
            session: 数据库会话
            role_id: 角色 ID
            user_ids: 用户 ID 列表

        Returns:
            成功添加的数量
        """
        # 获取角色信息
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            raise ValueError("角色不存在")

        tenant_id = role.tenant_id
        added = 0

        for user_id in user_ids:
            # 检查是否已存在
            stmt = select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                continue

            ur = UserRole(user_id=user_id, role_id=role_id, tenant_id=tenant_id)
            session.add(ur)
            added += 1

        await session.flush()
        _logger.info(f"角色批量添加成员: {role_id} -> {added} 人")
        return added

    @staticmethod
    async def remove_role_member(
        session: AsyncSession, role_id: str, user_id: str
    ) -> bool:
        """
        删除角色成员

        Args:
            session: 数据库会话
            role_id: 角色 ID
            user_id: 用户 ID

        Returns:
            是否移除成功
        """
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        result = await session.execute(stmt)
        ur = result.scalar_one_or_none()

        if ur:
            await session.delete(ur)
            await session.flush()
            _logger.info(f"移除角色成员: role={role_id}, user={user_id}")
            return True
        return False

    @staticmethod
    async def get_role_menus(session: AsyncSession, role_id: str) -> list[str]:
        """
        获取角色已分配的菜单 ID 列表

        通过 RolePermission + MenuPermission 间接获取角色关联的菜单。

        Args:
            session: 数据库会话
            role_id: 角色 ID

        Returns:
            list[str]: 菜单 ID 列表
        """
        from iam.models import MenuPermission

        # 获取角色的权限 ID
        stmt = select(RolePermission.permission_id).where(
            RolePermission.role_id == role_id
        )
        result = await session.execute(stmt)
        perm_ids = [row[0] for row in result.fetchall()]

        if not perm_ids:
            return []

        # 通过 MenuPermission 获取关联的菜单 ID
        stmt = (
            select(MenuPermission.menu_id)
            .where(MenuPermission.permission_id.in_(perm_ids))
            .distinct()
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.fetchall()]

    @staticmethod
    async def assign_role_menus(
        session: AsyncSession, role_id: str, menu_ids: list[str]
    ) -> None:
        """
        为角色分配菜单（通过权限间接分配）

        将菜单关联的所有权限分配给角色（覆盖式）。

        Args:
            session: 数据库会话
            role_id: 角色 ID
            menu_ids: 菜单 ID 列表
        """
        from iam.models import MenuPermission

        # 获取角色信息
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            raise ValueError("角色不存在")

        if role.is_system:
            raise ValueError("系统内置角色禁止修改")

        # 获取菜单关联的所有权限 ID
        stmt = (
            select(MenuPermission.permission_id)
            .where(MenuPermission.menu_id.in_(menu_ids))
            .distinct()
        )
        result = await session.execute(stmt)
        perm_ids = [row[0] for row in result.fetchall()]

        # 删除现有权限（仅 MenuPermission 关联的权限）
        existing_menu_perms_stmt = select(MenuPermission.permission_id).distinct()
        existing_result = await session.execute(existing_menu_perms_stmt)
        existing_menu_perm_ids = {row[0] for row in existing_result.fetchall()}

        # 删除角色现有的、属于菜单权限的权限分配
        stmt = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id.in_(existing_menu_perm_ids),
        )
        result = await session.execute(stmt)
        for rp in result.scalars().all():
            await session.delete(rp)

        # 添加新权限（仅添加菜单关联的权限）
        actual_tenant_id = role.tenant_id
        for perm_id in perm_ids:
            rp = RolePermission(
                role_id=role_id,
                permission_id=perm_id,
                tenant_id=actual_tenant_id,
            )
            session.add(rp)

        await session.flush()
        _logger.info(
            f"角色分配菜单: {role_id} -> {len(menu_ids)} menus, {len(perm_ids)} permissions"
        )


# 服务单例
role_service = RoleService()
user_role_service = UserRoleService()
role_member_service = RoleMemberService()
