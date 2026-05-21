"""
角色管理服务

提供角色 CRUD 和权限分配功能。
"""

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from models.iam import Permission, Role, RolePermission, UserRole
from framework.database.core.engine import async_session

_logger = logger.bind(name=__name__)


class RoleService:
    """角色管理服务"""

    @staticmethod
    async def create(
        code: str,
        name: str,
        tenant_id: str | None = None,
        description: str | None = None,
        is_system: bool = False,
    ) -> Role:
        """
        创建角色

        Args:
            code: 角色编码
            name: 角色名称
            tenant_id: 租户 ID（None 为全局角色）
            description: 描述
            is_system: 是否系统内置

        Returns:
            Role
        """
        async with async_session() as session:
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
            await session.commit()
            await session.refresh(role)

            _logger.info(f"创建角色: {code}")
            return role

    @staticmethod
    async def get_by_id(role_id: str) -> Role | None:
        """根据 ID 获取角色"""
        async with async_session() as session:
            stmt = select(Role).where(Role.id == role_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def update(
        role_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> Role:
        """更新角色"""
        async with async_session() as session:
            stmt = select(Role).where(Role.id == role_id)
            result = await session.execute(stmt)
            role = result.scalar_one_or_none()

            if not role:
                raise ValueError("角色不存在")

            if name is not None:
                role.name = name
            if description is not None:
                role.description = description

            await session.commit()
            await session.refresh(role)

            _logger.info(f"更新角色: {role_id}")
            return role

    @staticmethod
    async def delete(role_id: str) -> bool:
        """删除角色"""
        async with async_session() as session:
            stmt = select(Role).where(Role.id == role_id)
            result = await session.execute(stmt)
            role = result.scalar_one_or_none()

            if not role:
                return False

            if role.is_system:
                raise ValueError("系统内置角色不可删除")

            await session.delete(role)
            await session.commit()

            _logger.info(f"删除角色: {role_id}")
            return True

    @staticmethod
    async def list_roles(
        tenant_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Role], int]:
        """获取角色列表"""
        async with async_session() as session:
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
    async def assign_permissions(role_id: str, permission_ids: list[str]) -> None:
        """为角色分配权限"""
        async with async_session() as session:
            # 删除现有权限
            stmt = select(RolePermission).where(RolePermission.role_id == role_id)
            result = await session.execute(stmt)
            for rp in result.scalars().all():
                await session.delete(rp)

            # 添加新权限
            for perm_id in permission_ids:
                rp = RolePermission(role_id=role_id, permission_id=perm_id)
                session.add(rp)

            await session.commit()
            _logger.info(f"角色分配权限: {role_id} -> {len(permission_ids)} permissions")

    @staticmethod
    async def get_role_permissions(role_id: str) -> list[Permission]:
        """获取角色的权限列表"""
        async with async_session() as session:
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
    async def assign_roles(user_id: str, role_ids: list[str]) -> None:
        """为用户分配角色"""
        async with async_session() as session:
            # 删除现有角色
            stmt = select(UserRole).where(UserRole.user_id == user_id)
            result = await session.execute(stmt)
            for ur in result.scalars().all():
                await session.delete(ur)

            # 添加新角色
            for role_id in role_ids:
                ur = UserRole(user_id=user_id, role_id=role_id)
                session.add(ur)

            await session.commit()
            _logger.info(f"用户分配角色: {user_id} -> {len(role_ids)} roles")

    @staticmethod
    async def get_user_roles(user_id: str) -> list[Role]:
        """获取用户的角色列表"""
        async with async_session() as session:
            stmt = (
                select(Role)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(UserRole.user_id == user_id)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def remove_role(user_id: str, role_id: str) -> bool:
        """移除用户的某个角色"""
        async with async_session() as session:
            stmt = select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
            result = await session.execute(stmt)
            ur = result.scalar_one_or_none()

            if ur:
                await session.delete(ur)
                await session.commit()
                return True
            return False


# 服务单例
role_service = RoleService()
user_role_service = UserRoleService()
