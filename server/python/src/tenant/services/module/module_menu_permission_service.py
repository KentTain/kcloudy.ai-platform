"""
模块菜单权限关联服务层
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.events import (
    ModuleMenuPermissionCreated,
    ModuleMenuPermissionDeleted,
    event_publisher,
)
from tenant.models import ModuleMenu, ModuleMenuPermission, ModulePermission

_logger = logging.getLogger(__name__)


class ModuleMenuPermissionService:
    """模块菜单权限关联服务"""

    @staticmethod
    async def get_menu_permissions(
        session: AsyncSession,
        menu_id: str,
    ) -> list[ModulePermission]:
        """
        获取菜单关联的权限列表

        Args:
            session: 数据库会话
            menu_id: 菜单 ID

        Returns:
            权限列表
        """
        stmt = (
            select(ModulePermission)
            .join(
                ModuleMenuPermission,
                ModulePermission.id == ModuleMenuPermission.module_permission_id,
            )
            .where(ModuleMenuPermission.module_menu_id == menu_id)
            .order_by(ModulePermission.resource.asc(), ModulePermission.action.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_menu_permissions(
        session: AsyncSession,
        menu_id: str,
        permission_ids: list[str],
    ) -> list[ModulePermission]:
        """
        更新菜单的权限列表（整体替换）

        Args:
            session: 数据库会话
            menu_id: 菜单 ID
            permission_ids: 新的权限 ID 列表

        Returns:
            更新后的权限列表

        Raises:
            ValueError: 菜单不存在或权限不属于同一模块
        """
        # 检查菜单是否存在
        menu_stmt = select(ModuleMenu).where(ModuleMenu.id == menu_id)
        menu_result = await session.execute(menu_stmt)
        menu = menu_result.scalar_one_or_none()

        if not menu:
            raise ValueError(f"菜单不存在: {menu_id}")

        # 获取模块的所有权限，验证 permission_ids 都属于该模块
        perm_stmt = select(ModulePermission).where(
            ModulePermission.module_id == menu.module_id
        )
        perm_result = await session.execute(perm_stmt)
        module_permissions = {p.id: p for p in perm_result.scalars().all()}

        # 验证所有 permission_id 都属于该模块
        invalid_ids = set(permission_ids) - set(module_permissions.keys())
        if invalid_ids:
            raise ValueError(f"权限不属于该模块: {invalid_ids}")

        # 删除现有权限关联
        delete_stmt = select(ModuleMenuPermission).where(
            ModuleMenuPermission.module_menu_id == menu_id
        )
        delete_result = await session.execute(delete_stmt)
        for mp in delete_result.scalars().all():
            await session.delete(mp)

        # 添加新的权限关联
        for perm_id in permission_ids:
            mp = ModuleMenuPermission(
                module_menu_id=menu_id,
                module_permission_id=perm_id,
            )
            session.add(mp)

        await session.flush()

        _logger.info(f"更新菜单 {menu_id} 的权限: {len(permission_ids)} 个")

        # 返回更新后的权限列表
        return [module_permissions[pid] for pid in permission_ids]

    @staticmethod
    async def add_permission_to_menu(
        session: AsyncSession,
        menu_id: str,
        permission_id: str,
    ) -> ModuleMenuPermission:
        """
        添加权限到菜单

        Args:
            session: 数据库会话
            menu_id: 菜单 ID
            permission_id: 权限 ID

        Returns:
            ModuleMenuPermission

        Raises:
            ValueError: 菜单不存在、权限不存在或权限不属于同一模块
        """
        # 检查菜单是否存在
        menu_stmt = select(ModuleMenu).where(ModuleMenu.id == menu_id)
        menu_result = await session.execute(menu_stmt)
        menu = menu_result.scalar_one_or_none()

        if not menu:
            raise ValueError(f"菜单不存在: {menu_id}")

        # 检查权限是否存在且属于同一模块
        perm_stmt = select(ModulePermission).where(ModulePermission.id == permission_id)
        perm_result = await session.execute(perm_stmt)
        permission = perm_result.scalar_one_or_none()

        if not permission:
            raise ValueError(f"权限不存在: {permission_id}")

        if permission.module_id != menu.module_id:
            raise ValueError("权限不属于该菜单所在的模块")

        # 检查是否已存在关联
        existing_stmt = select(ModuleMenuPermission).where(
            ModuleMenuPermission.module_menu_id == menu_id,
            ModuleMenuPermission.module_permission_id == permission_id,
        )
        existing_result = await session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise ValueError("该权限已关联到此菜单")

        # 创建关联
        mp = ModuleMenuPermission(
            module_menu_id=menu_id,
            module_permission_id=permission_id,
        )
        session.add(mp)
        await session.flush()
        await session.refresh(mp)

        _logger.info(f"添加权限 {permission_id} 到菜单 {menu_id}")

        # 发布事件
        await event_publisher.publish(
            ModuleMenuPermissionCreated(
                module_menu_id=menu_id,
                module_permission_id=permission_id,
            )
        )

        return mp

    @staticmethod
    async def remove_permission_from_menu(
        session: AsyncSession,
        menu_id: str,
        permission_id: str,
    ) -> bool:
        """
        从菜单移除权限

        Args:
            session: 数据库会话
            menu_id: 菜单 ID
            permission_id: 权限 ID

        Returns:
            bool: 是否移除成功
        """
        # 查找关联记录
        stmt = select(ModuleMenuPermission).where(
            ModuleMenuPermission.module_menu_id == menu_id,
            ModuleMenuPermission.module_permission_id == permission_id,
        )
        result = await session.execute(stmt)
        mp = result.scalar_one_or_none()

        if not mp:
            return False

        await session.delete(mp)
        await session.flush()

        _logger.info(f"从菜单 {menu_id} 移除权限 {permission_id}")

        # 发布事件
        await event_publisher.publish(
            ModuleMenuPermissionDeleted(
                module_menu_id=menu_id,
                module_permission_id=permission_id,
            )
        )

        return True

    @staticmethod
    async def clear_menu_permissions(session: AsyncSession, menu_id: str) -> int:
        """
        清除菜单的所有权限关联

        Args:
            session: 数据库会话
            menu_id: 菜单 ID

        Returns:
            清除的关联数量
        """
        stmt = select(ModuleMenuPermission).where(
            ModuleMenuPermission.module_menu_id == menu_id
        )
        result = await session.execute(stmt)
        associations = list(result.scalars().all())

        for mp in associations:
            await session.delete(mp)

        await session.flush()

        if associations:
            _logger.info(f"清除菜单 {menu_id} 的 {len(associations)} 个权限关联")

        return len(associations)


# 单例实例
module_menu_permission_service = ModuleMenuPermissionService()
