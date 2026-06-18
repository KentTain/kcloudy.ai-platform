"""
模块权限服务层
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.events import (
    ModulePermissionCreated,
    ModulePermissionDeleted,
    ModulePermissionUpdated,
    event_publisher,
)
from tenant.models import ModulePermission, ModuleRolePermission

_logger = logging.getLogger(__name__)


class ModulePermissionService:
    """模块权限服务"""

    @staticmethod
    async def list_permissions(
        session: AsyncSession,
        module_id: str,
        page: int = 1,
        page_size: int = 100,
        resource: str | None = None,
        action: str | None = None,
    ) -> tuple[list[ModulePermission], int]:
        """
        查询模块权限列表

        Args:
            session: 数据库会话
            module_id: 模块 ID
            page: 页码
            page_size: 每页数量
            resource: 资源名称筛选
            action: 操作类型筛选

        Returns:
            (权限列表, 总数)
        """
        # 构建查询条件
        conditions = [ModulePermission.module_id == module_id]
        if resource:
            conditions.append(ModulePermission.resource == resource)
        if action:
            conditions.append(ModulePermission.action == action)

        # 查询总数
        count_stmt = select(func.count(ModulePermission.id)).where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        stmt = (
            select(ModulePermission)
            .where(*conditions)
            .order_by(ModulePermission.resource.asc(), ModulePermission.action.asc())
        )
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        permissions = list(result.scalars().all())

        return permissions, total

    @staticmethod
    async def list_all_by_module(session: AsyncSession, module_id: str) -> list[ModulePermission]:
        """获取模块的所有权限（不分页）"""
        stmt = (
            select(ModulePermission)
            .where(ModulePermission.module_id == module_id)
            .order_by(ModulePermission.resource.asc(), ModulePermission.action.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, permission_id: str) -> ModulePermission | None:
        """根据 ID 获取权限"""
        stmt = select(ModulePermission).where(ModulePermission.id == permission_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(session: AsyncSession, code: str) -> ModulePermission | None:
        """根据编码获取权限"""
        stmt = select(ModulePermission).where(ModulePermission.code == code)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_ids(session: AsyncSession, permission_ids: list[str]) -> list[ModulePermission]:
        """根据 ID 列表获取权限"""
        if not permission_ids:
            return []
        stmt = select(ModulePermission).where(ModulePermission.id.in_(permission_ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        module_id: str,
        code: str,
        name: str,
        resource: str,
        action: str,
        description: str | None = None,
    ) -> ModulePermission:
        """
        创建模块权限

        Args:
            session: 数据库会话
            module_id: 模块 ID
            code: 权限编码
            name: 权限名称
            resource: 资源名称
            action: 操作类型（read/write/delete）
            description: 权限描述

        Returns:
            ModulePermission
        """
        permission = ModulePermission(
            module_id=module_id,
            code=code,
            name=name,
            resource=resource,
            action=action,
            description=description,
        )
        session.add(permission)
        await session.flush()
        await session.refresh(permission)

        _logger.info(f"创建模块权限: {permission.id} ({permission.code})")

        # 发布 ModulePermissionCreated 事件
        await event_publisher.publish(
            ModulePermissionCreated(
                module_permission_id=permission.id, module_id=module_id
            )
        )

        return permission

    @staticmethod
    async def update(
        session: AsyncSession,
        permission_id: str,
        name: str | None = None,
        resource: str | None = None,
        action: str | None = None,
        description: str | None = None,
    ) -> ModulePermission | None:
        """
        更新模块权限

        Args:
            session: 数据库会话
            permission_id: 权限 ID
            其他参数为要更新的字段

        Returns:
            ModulePermission | None
        """
        stmt = select(ModulePermission).where(ModulePermission.id == permission_id)
        result = await session.execute(stmt)
        permission = result.scalar_one_or_none()

        if not permission:
            return None

        if name is not None:
            permission.name = name
        if resource is not None:
            permission.resource = resource
        if action is not None:
            permission.action = action
        if description is not None:
            permission.description = description

        await session.flush()
        await session.refresh(permission)

        # 发布 ModulePermissionUpdated 事件
        await event_publisher.publish(
            ModulePermissionUpdated(
                module_permission_id=permission.id, module_id=permission.module_id
            )
        )

        return permission

    @staticmethod
    async def delete(session: AsyncSession, permission_id: str) -> bool:
        """
        删除模块权限

        Args:
            session: 数据库会话
            permission_id: 权限 ID

        Returns:
            bool: 是否删除成功

        Raises:
            ValueError: 权限已被角色引用，无法删除
        """
        stmt = select(ModulePermission).where(ModulePermission.id == permission_id)
        result = await session.execute(stmt)
        permission = result.scalar_one_or_none()

        if not permission:
            return False

        # 检查是否被角色引用
        ref_stmt = select(func.count(ModuleRolePermission.id)).where(
            ModuleRolePermission.module_permission_id == permission_id
        )
        ref_result = await session.execute(ref_stmt)
        ref_count = ref_result.scalar() or 0

        if ref_count > 0:
            raise ValueError(
                f"权限 {permission.code} 已被 {ref_count} 个角色引用，无法删除"
            )

        # 保存权限信息用于事件发布
        module_id = permission.module_id
        permission_code = permission.code

        await session.delete(permission)
        await session.flush()

        _logger.info(f"删除模块权限: {permission_id}")

        # 发布 ModulePermissionDeleted 事件
        await event_publisher.publish(
            ModulePermissionDeleted(module_id=module_id, permission_code=permission_code)
        )

        return True

    @staticmethod
    async def delete_by_module(session: AsyncSession, module_id: str) -> int:
        """
        删除模块的所有权限

        Args:
            session: 数据库会话
            module_id: 模块 ID

        Returns:
            删除的数量
        """
        stmt = select(ModulePermission).where(ModulePermission.module_id == module_id)
        result = await session.execute(stmt)
        permissions = list(result.scalars().all())

        count = len(permissions)
        for permission in permissions:
            await session.delete(permission)

        await session.flush()

        _logger.info(f"删除模块 {module_id} 的 {count} 个权限")
        return count
