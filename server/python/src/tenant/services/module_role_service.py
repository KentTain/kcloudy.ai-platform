"""
模块角色服务层
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from framework.events import (
    ModuleRoleCreated,
    ModuleRoleDeleted,
    ModuleRolePermissionChanged,
    ModuleRoleUpdated,
    event_publisher,
)
from tenant.models import ModulePermission, ModuleRole, ModuleRolePermission

_logger = logging.getLogger(__name__)


class ModuleRoleService:
    """模块角色服务"""

    @staticmethod
    async def list_roles(
        session: AsyncSession,
        module_id: str,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[ModuleRole], int]:
        """
        查询模块角色列表

        Args:
            session: 数据库会话
            module_id: 模块 ID
            page: 页码
            page_size: 每页数量

        Returns:
            (角色列表, 总数)
        """
        # 查询总数
        count_stmt = select(func.count(ModuleRole.id)).where(
            ModuleRole.module_id == module_id
        )
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        stmt = (
            select(ModuleRole)
            .where(ModuleRole.module_id == module_id)
            .order_by(ModuleRole.is_system.desc(), ModuleRole.created_at.asc())
        )
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        roles = list(result.scalars().all())

        return roles, total

    @staticmethod
    async def list_all_by_module(session: AsyncSession, module_id: str) -> list[ModuleRole]:
        """获取模块的所有角色（不分页）"""
        stmt = (
            select(ModuleRole)
            .where(ModuleRole.module_id == module_id)
            .order_by(ModuleRole.is_system.desc(), ModuleRole.created_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, role_id: str) -> ModuleRole | None:
        """根据 ID 获取角色"""
        stmt = select(ModuleRole).where(ModuleRole.id == role_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(session: AsyncSession, module_id: str, code: str) -> ModuleRole | None:
        """根据模块 ID 和编码获取角色"""
        stmt = select(ModuleRole).where(
            ModuleRole.module_id == module_id,
            ModuleRole.code == code,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        module_id: str,
        code: str,
        name: str,
        description: str | None = None,
        is_system: bool = False,
    ) -> ModuleRole:
        """
        创建模块角色

        Args:
            session: 数据库会话
            module_id: 模块 ID
            code: 角色编码
            name: 角色名称
            description: 角色描述
            is_system: 是否系统内置角色

        Returns:
            ModuleRole
        """
        role = ModuleRole(
            module_id=module_id,
            code=code,
            name=name,
            description=description,
            is_system=is_system,
        )
        session.add(role)
        await session.flush()
        await session.refresh(role)

        _logger.info(f"创建模块角色: {role.id} ({role.code})")

        # 发布 ModuleRoleCreated 事件
        await event_publisher.publish(
            ModuleRoleCreated(module_role_id=role.id, module_id=module_id)
        )

        return role

    @staticmethod
    async def update(
        session: AsyncSession,
        role_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> ModuleRole | None:
        """
        更新模块角色

        系统内置角色禁止更新。

        Args:
            session: 数据库会话
            role_id: 角色 ID
            name: 角色名称
            description: 角色描述

        Returns:
            ModuleRole | None

        Raises:
            ValueError: 系统内置角色禁止更新
        """
        stmt = select(ModuleRole).where(ModuleRole.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            return None

        if role.is_system:
            raise ValueError(f"系统内置角色 {role.name} 禁止修改")

        if name is not None:
            role.name = name
        if description is not None:
            role.description = description

        await session.flush()
        await session.refresh(role)

        # 发布 ModuleRoleUpdated 事件
        await event_publisher.publish(
            ModuleRoleUpdated(module_role_id=role.id, module_id=role.module_id)
        )

        return role

    @staticmethod
    async def delete(session: AsyncSession, role_id: str) -> bool:
        """
        删除模块角色

        系统内置角色禁止删除。

        Args:
            session: 数据库会话
            role_id: 角色 ID

        Returns:
            bool: 是否删除成功

        Raises:
            ValueError: 系统内置角色禁止删除
        """
        stmt = select(ModuleRole).where(ModuleRole.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            return False

        if role.is_system:
            raise ValueError(f"系统内置角色 {role.name} 禁止删除")

        # 保存角色信息用于事件发布
        module_id = role.module_id
        role_code = role.code

        await session.delete(role)
        await session.flush()

        _logger.info(f"删除模块角色: {role_id}")

        # 发布 ModuleRoleDeleted 事件
        await event_publisher.publish(
            ModuleRoleDeleted(module_id=module_id, role_code=role_code)
        )

        return True

    # =========================================================================
    # 角色权限关联管理
    # =========================================================================

    @staticmethod
    async def get_role_permissions(session: AsyncSession, role_id: str) -> list[ModulePermission]:
        """
        获取角色的权限列表

        Args:
            session: 数据库会话
            role_id: 角色 ID

        Returns:
            权限列表
        """
        stmt = (
            select(ModulePermission)
            .join(
                ModuleRolePermission,
                ModulePermission.id == ModuleRolePermission.module_permission_id,
            )
            .where(ModuleRolePermission.module_role_id == role_id)
            .order_by(ModulePermission.resource.asc(), ModulePermission.action.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_role_permissions(
        session: AsyncSession,
        role_id: str,
        permission_ids: list[str],
    ) -> list[ModulePermission]:
        """
        更新角色的权限列表（整体替换）

        系统内置角色禁止更新权限。

        Args:
            session: 数据库会话
            role_id: 角色 ID
            permission_ids: 新的权限 ID 列表

        Returns:
            更新后的权限列表

        Raises:
            ValueError: 系统内置角色禁止更新权限
        """
        # 检查角色是否存在
        stmt = select(ModuleRole).where(ModuleRole.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise ValueError(f"角色不存在: {role_id}")

        if role.is_system:
            raise ValueError(f"系统内置角色 {role.name} 禁止修改权限")

        # 获取模块的所有权限，验证 permission_ids 都属于该模块
        perm_stmt = select(ModulePermission).where(
            ModulePermission.module_id == role.module_id
        )
        perm_result = await session.execute(perm_stmt)
        module_permissions = {p.id: p for p in perm_result.scalars().all()}

        # 验证所有 permission_id 都属于该模块
        invalid_ids = set(permission_ids) - set(module_permissions.keys())
        if invalid_ids:
            raise ValueError(f"权限不属于该模块: {invalid_ids}")

        # 删除现有权限关联
        delete_stmt = select(ModuleRolePermission).where(
            ModuleRolePermission.module_role_id == role_id
        )
        delete_result = await session.execute(delete_stmt)
        for rp in delete_result.scalars().all():
            await session.delete(rp)

        # 添加新的权限关联
        for perm_id in permission_ids:
            rp = ModuleRolePermission(
                module_role_id=role_id,
                module_permission_id=perm_id,
            )
            session.add(rp)

        await session.flush()

        _logger.info(f"更新角色 {role_id} 的权限: {len(permission_ids)} 个")

        # 发布 ModuleRolePermissionChanged 事件
        await event_publisher.publish(
            ModuleRolePermissionChanged(module_role_id=role_id, module_id=role.module_id)
        )

        # 返回更新后的权限列表
        return [module_permissions[pid] for pid in permission_ids]

    @staticmethod
    async def set_role_all_permissions(session: AsyncSession, role_id: str) -> int:
        """
        为角色设置模块的所有权限

        用于管理员角色初始化。

        Args:
            session: 数据库会话
            role_id: 角色 ID

        Returns:
            设置的权限数量
        """
        # 获取角色
        stmt = select(ModuleRole).where(ModuleRole.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise ValueError(f"角色不存在: {role_id}")

        # 获取模块所有权限
        perm_stmt = select(ModulePermission).where(
            ModulePermission.module_id == role.module_id
        )
        perm_result = await session.execute(perm_stmt)
        permissions = list(perm_result.scalars().all())

        # 删除现有权限关联
        delete_stmt = select(ModuleRolePermission).where(
            ModuleRolePermission.module_role_id == role_id
        )
        delete_result = await session.execute(delete_stmt)
        for rp in delete_result.scalars().all():
            await session.delete(rp)

        # 添加所有权限关联
        for perm in permissions:
            rp = ModuleRolePermission(
                module_role_id=role_id,
                module_permission_id=perm.id,
            )
            session.add(rp)

        await session.flush()

        _logger.info(f"为角色 {role_id} 设置所有权限: {len(permissions)} 个")

        # 发布 ModuleRolePermissionChanged 事件
        await event_publisher.publish(
            ModuleRolePermissionChanged(module_role_id=role_id, module_id=role.module_id)
        )

        return len(permissions)

    @staticmethod
    async def set_role_read_permissions(session: AsyncSession, role_id: str) -> int:
        """
        为角色设置模块的读取权限

        用于普通用户角色初始化。

        Args:
            session: 数据库会话
            role_id: 角色 ID

        Returns:
            设置的权限数量
        """
        # 获取角色
        stmt = select(ModuleRole).where(ModuleRole.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise ValueError(f"角色不存在: {role_id}")

        # 获取模块的读取权限
        perm_stmt = select(ModulePermission).where(
            ModulePermission.module_id == role.module_id,
            ModulePermission.action == "read",
        )
        perm_result = await session.execute(perm_stmt)
        permissions = list(perm_result.scalars().all())

        # 删除现有权限关联
        delete_stmt = select(ModuleRolePermission).where(
            ModuleRolePermission.module_role_id == role_id
        )
        delete_result = await session.execute(delete_stmt)
        for rp in delete_result.scalars().all():
            await session.delete(rp)

        # 添加读取权限关联
        for perm in permissions:
            rp = ModuleRolePermission(
                module_role_id=role_id,
                module_permission_id=perm.id,
            )
            session.add(rp)

        await session.flush()

        _logger.info(f"为角色 {role_id} 设置读取权限: {len(permissions)} 个")

        # 发布 ModuleRolePermissionChanged 事件
        await event_publisher.publish(
            ModuleRolePermissionChanged(module_role_id=role_id, module_id=role.module_id)
        )

        return len(permissions)

    @staticmethod
    async def get_roles_with_permissions(session: AsyncSession, module_id: str) -> list[dict]:
        """
        获取模块的所有角色及其权限

        Args:
            session: 数据库会话
            module_id: 模块 ID

        Returns:
            角色列表（包含权限信息）
        """
        roles = await ModuleRoleService.list_all_by_module(session, module_id)
        result = []
        for role in roles:
            permissions = await ModuleRoleService.get_role_permissions(session, role.id)
            result.append({
                "id": role.id,
                "module_id": role.module_id,
                "code": role.code,
                "name": role.name,
                "description": role.description,
                "is_system": role.is_system,
                "created_at": role.created_at,
                "updated_at": role.updated_at,
                "permissions": [
                    {
                        "id": p.id,
                        "module_id": p.module_id,
                        "code": p.code,
                        "name": p.name,
                        "resource": p.resource,
                        "action": p.action,
                        "description": p.description,
                        "created_at": p.created_at,
                        "updated_at": p.updated_at,
                    }
                    for p in permissions
                ],
            })
        return result
