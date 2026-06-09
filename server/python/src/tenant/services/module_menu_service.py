"""
模块菜单服务层
"""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from framework.database.core.engine import async_session
from framework.events import (
    ModuleMenuCreated,
    ModuleMenuDeleted,
    ModuleMenuUpdated,
    event_publisher,
)
from tenant.models import ModuleMenu

_logger = logging.getLogger(__name__)


class ModuleMenuService:
    """模块菜单服务"""

    @staticmethod
    async def list_menus(module_id: str) -> list[ModuleMenu]:
        """
        查询模块菜单列表

        Args:
            module_id: 模块 ID

        Returns:
            菜单列表（按 sort_order 排序）
        """
        async with async_session() as session:
            stmt = (
                select(ModuleMenu)
                .where(ModuleMenu.module_id == module_id)
                .order_by(ModuleMenu.sort_order.asc(), ModuleMenu.created_at.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    def build_tree(menus: list[ModuleMenu]) -> list[dict[str, Any]]:
        """
        构建菜单树形结构

        Args:
            menus: 扁平菜单列表

        Returns:
            树形结构菜单列表
        """
        # 构建菜单映射
        menu_map: dict[str, dict[str, Any]] = {}
        for menu in menus:
            menu_map[menu.id] = {
                "id": menu.id,
                "module_id": menu.module_id,
                "parent_id": menu.parent_id,
                "code": menu.code,
                "name": menu.name,
                "path": menu.path,
                "icon": menu.icon,
                "sort_order": menu.sort_order,
                "is_visible": menu.is_visible,
                "created_at": menu.created_at,
                "updated_at": menu.updated_at,
                "children": [],
            }

        # 构建树形结构
        root_menus: list[dict[str, Any]] = []
        for menu_dict in menu_map.values():
            parent_id = menu_dict["parent_id"]
            if parent_id is None or parent_id not in menu_map:
                root_menus.append(menu_dict)
            else:
                menu_map[parent_id]["children"].append(menu_dict)

        # 递归排序子菜单
        def sort_children(menu_dict: dict[str, Any]) -> None:
            menu_dict["children"].sort(key=lambda x: (x["sort_order"], x["created_at"]))
            for child in menu_dict["children"]:
                sort_children(child)

        for root in root_menus:
            sort_children(root)

        return root_menus

    @staticmethod
    async def get_by_id(menu_id: str) -> ModuleMenu | None:
        """根据 ID 获取菜单"""
        async with async_session() as session:
            stmt = select(ModuleMenu).where(ModuleMenu.id == menu_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(code: str) -> ModuleMenu | None:
        """根据编码获取菜单"""
        async with async_session() as session:
            stmt = select(ModuleMenu).where(ModuleMenu.code == code)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def create(
        module_id: str,
        code: str,
        name: str,
        path: str,
        parent_id: str | None = None,
        icon: str | None = None,
        sort_order: int = 0,
        is_visible: bool = True,
    ) -> ModuleMenu:
        """
        创建模块菜单

        Args:
            module_id: 模块 ID
            code: 菜单编码
            name: 菜单名称
            path: 前端路由路径
            parent_id: 父菜单 ID
            icon: 图标标识
            sort_order: 排序号
            is_visible: 是否显示

        Returns:
            ModuleMenu
        """
        async with async_session() as session:
            menu = ModuleMenu(
                module_id=module_id,
                parent_id=parent_id,
                code=code,
                name=name,
                path=path,
                icon=icon,
                sort_order=sort_order,
                is_visible=is_visible,
            )
            session.add(menu)
            await session.commit()
            await session.refresh(menu)

            _logger.info(f"创建模块菜单: {menu.id} ({menu.code})")

            # 发布 ModuleMenuCreated 事件
            await event_publisher.publish(
                ModuleMenuCreated(module_menu_id=menu.id, module_id=module_id)
            )

            return menu

    @staticmethod
    async def update(
        menu_id: str,
        name: str | None = None,
        path: str | None = None,
        parent_id: str | None = None,
        icon: str | None = None,
        sort_order: int | None = None,
        is_visible: bool | None = None,
    ) -> ModuleMenu | None:
        """
        更新模块菜单

        Args:
            menu_id: 菜单 ID
            其他参数为要更新的字段

        Returns:
            ModuleMenu | None
        """
        async with async_session() as session:
            stmt = select(ModuleMenu).where(ModuleMenu.id == menu_id)
            result = await session.execute(stmt)
            menu = result.scalar_one_or_none()

            if not menu:
                return None

            if name is not None:
                menu.name = name
            if path is not None:
                menu.path = path
            if parent_id is not None:
                # 检查是否会导致循环引用
                if parent_id == menu_id:
                    raise ValueError("菜单不能以自己为父菜单")
                menu.parent_id = parent_id
            if icon is not None:
                menu.icon = icon
            if sort_order is not None:
                menu.sort_order = sort_order
            if is_visible is not None:
                menu.is_visible = is_visible

            await session.commit()
            await session.refresh(menu)

            # 发布 ModuleMenuUpdated 事件
            await event_publisher.publish(
                ModuleMenuUpdated(module_menu_id=menu.id, module_id=menu.module_id)
            )

            return menu

    @staticmethod
    async def delete(menu_id: str) -> bool:
        """
        删除模块菜单

        检查是否有子菜单，若有则禁止删除。

        Args:
            menu_id: 菜单 ID

        Returns:
            bool: 是否删除成功

        Raises:
            ValueError: 菜单有子菜单，无法删除
        """
        async with async_session() as session:
            # 检查菜单是否存在
            stmt = select(ModuleMenu).where(ModuleMenu.id == menu_id)
            result = await session.execute(stmt)
            menu = result.scalar_one_or_none()

            if not menu:
                return False

            # 检查是否有子菜单
            child_count_stmt = select(func.count(ModuleMenu.id)).where(
                ModuleMenu.parent_id == menu_id
            )
            child_count_result = await session.execute(child_count_stmt)
            child_count = child_count_result.scalar() or 0

            if child_count > 0:
                raise ValueError(f"菜单 {menu.name} 有 {child_count} 个子菜单，无法删除")

            # 保存菜单信息用于事件发布
            module_id = menu.module_id
            menu_code = menu.code

            await session.delete(menu)
            await session.commit()

            _logger.info(f"删除模块菜单: {menu_id}")

            # 发布 ModuleMenuDeleted 事件
            await event_publisher.publish(
                ModuleMenuDeleted(module_id=module_id, menu_code=menu_code)
            )

            return True

    @staticmethod
    async def has_children(menu_id: str) -> bool:
        """检查菜单是否有子菜单"""
        async with async_session() as session:
            stmt = select(func.count(ModuleMenu.id)).where(
                ModuleMenu.parent_id == menu_id
            )
            result = await session.execute(stmt)
            count = result.scalar() or 0
            return count > 0

    @staticmethod
    async def get_children(menu_id: str) -> list[ModuleMenu]:
        """获取菜单的所有子菜单"""
        async with async_session() as session:
            stmt = (
                select(ModuleMenu)
                .where(ModuleMenu.parent_id == menu_id)
                .order_by(ModuleMenu.sort_order.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_all_descendants(menu_id: str) -> list[str]:
        """
        获取菜单的所有后代菜单 ID

        Args:
            menu_id: 菜单 ID

        Returns:
            后代菜单 ID 列表（包含自身）
        """
        descendants: list[str] = [menu_id]
        children = await ModuleMenuService.get_children(menu_id)
        for child in children:
            descendants.extend(await ModuleMenuService.get_all_descendants(child.id))
        return descendants
