"""
菜单管理服务

提供用户菜单查询功能。
"""

from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import Menu, MenuPermission, Permission, Role, RolePermission, UserRole

_logger = logger.bind(name=__name__)

# 类型别名：菜单树字典
MenuTreeDict = dict[str, Any]


class MenuService:
    """菜单管理服务"""

    @staticmethod
    async def get_user_menus(session: AsyncSession, user_id: str) -> list[MenuTreeDict]:
        """
        获取用户可见菜单树

        场景：已登录用户获取菜单
        WHEN 已登录用户请求菜单列表
        THEN 系统返回该用户有权限查看的菜单树

        场景：用户无任何菜单权限
        WHEN 用户没有任何菜单权限
        THEN 系统返回空数组

        场景：菜单无权限限制
        WHEN 菜单未关联任何权限
        THEN 所有登录用户可见此菜单（is_visible = true 时）
        """
        from iam.schemas.menu import MenuTreeNode

        # 1. 获取用户的所有权限 ID
        stmt = (
            select(Permission.id)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, RolePermission.role_id == Role.id)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )
        result = await session.execute(stmt)
        user_permission_ids = {row[0] for row in result.fetchall()}

        # 2. 查询所有可见菜单
        stmt = (
            select(Menu)
            .where(Menu.is_visible.is_(True))
            .order_by(Menu.tree_sorts)
        )
        result = await session.execute(stmt)
        all_menus = list(result.scalars().all())

        if not all_menus:
            return []

        # 3. 获取所有菜单的权限关联
        menu_ids = [m.id for m in all_menus]
        stmt = select(MenuPermission).where(MenuPermission.menu_id.in_(menu_ids))
        result = await session.execute(stmt)
        menu_permissions = list(result.scalars().all())

        # 构建 menu_id -> permission_ids 映射
        menu_permission_map: dict[str, set[str]] = {}
        for mp in menu_permissions:
            if mp.menu_id not in menu_permission_map:
                menu_permission_map[mp.menu_id] = set()
            menu_permission_map[mp.menu_id].add(mp.permission_id)

        # 4. 过滤菜单：无权限限制 OR 用户拥有任一权限
        visible_menu_ids = set()
        for menu in all_menus:
            menu_perms = menu_permission_map.get(menu.id, set())
            # 无权限限制的菜单，所有登录用户可见
            if not menu_perms or menu_perms & user_permission_ids:
                visible_menu_ids.add(menu.id)

        # 5. 过滤菜单列表并构建树
        visible_menus = [m for m in all_menus if m.id in visible_menu_ids]

        # 使用 transform_func 将 ORM 模型转换为字典
        def transform(menu: Menu) -> dict:
            return MenuTreeNode.from_menu(menu).model_dump()

        return Menu.build_tree(visible_menus, transform_func=transform)

    @staticmethod
    async def get_all_menus(session: AsyncSession) -> list[MenuTreeDict]:
        """获取所有菜单树（管理用）"""
        from iam.schemas.menu import MenuTreeNode

        stmt = select(Menu).order_by(Menu.tree_sorts)
        result = await session.execute(stmt)
        menus = list(result.scalars().all())

        # 使用 transform_func 将 ORM 模型转换为字典
        def transform(menu: Menu) -> dict:
            return MenuTreeNode.from_menu(menu).model_dump()

        return Menu.build_tree(menus, transform_func=transform)


# 服务单例
menu_service = MenuService()


# 服务单例
menu_service = MenuService()
