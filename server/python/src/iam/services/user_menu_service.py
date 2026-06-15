"""
用户菜单服务

提供用户菜单查询和权限过滤功能。
"""

from typing import Any

from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from framework.database.core.engine import async_session
from iam.models import Menu, MenuPermission, Permission, Role, RolePermission, UserRole
from tenant.models import Module, TenantModule

_logger = logger.bind(name=__name__)

# 类型别名
MenuTreeDict = dict[str, Any]


class UserMenuService:
    """用户菜单服务"""

    @staticmethod
    async def get_user_menus(user_id: str, tenant_id: str | None = None) -> list[MenuTreeDict]:
        """
        获取用户可见菜单树

        根据用户权限过滤菜单，返回用户有权限访问的菜单树。

        场景：已登录用户获取菜单
        WHEN 已登录用户请求菜单列表
        THEN 系统返回该用户有权限查看的菜单树

        场景：用户无任何菜单权限
        WHEN 用户没有任何菜单权限
        THEN 系统返回空数组

        场景：菜单无权限限制
        WHEN 菜单未关联任何权限
        THEN 所有登录用户可见此菜单（is_visible = true 时）

        Args:
            user_id: 用户 ID
            tenant_id: 租户 ID（可选）

        Returns:
            list[MenuTreeDict]: 菜单树列表
        """
        async with async_session() as session:
            # 1. 获取租户已分配且启用的模块
            enabled_module_ids = await UserMenuService._get_enabled_modules(
                session, tenant_id
            )

            if not enabled_module_ids:
                _logger.info(f"租户 {tenant_id} 无已分配的启用模块")
                return []

            # 2. 获取用户的所有权限 ID
            user_permission_ids = await UserMenuService._get_user_permissions(
                session, user_id, tenant_id
            )

            # 3. 查询所有可见菜单（按树排序）
            all_menus = await UserMenuService._get_visible_menus(
                session, tenant_id, enabled_module_ids
            )

            if not all_menus:
                return []

            # 4. 获取菜单的权限关联
            menu_ids = [m.id for m in all_menus]
            menu_permission_map = await UserMenuService._get_menu_permissions(
                session, menu_ids
            )

            # 5. 过滤菜单：无权限限制 OR 用户拥有任一权限
            visible_menu_ids = UserMenuService._filter_visible_menus(
                all_menus, menu_permission_map, user_permission_ids
            )

            # 6. 包含父菜单（子菜单有权限时，父菜单也需要显示）
            visible_menu_ids = UserMenuService._include_parent_menus(
                all_menus, visible_menu_ids
            )

            # 7. 构建菜单树
            visible_menus = [m for m in all_menus if m.id in visible_menu_ids]
            return UserMenuService._build_menu_tree(visible_menus)

    @staticmethod
    async def _get_enabled_modules(session, tenant_id: str | None) -> set[str]:
        """
        获取租户已分配且启用的模块 code

        Args:
            session: 数据库会话
            tenant_id: 租户 ID

        Returns:
            set[str]: 启用的模块 code 集合（如 "iam", "demo"）
        """
        # 构建查询：租户已分配的模块 + 模块启用状态
        # 返回 Module.code，因为 Menu.module 存储的是模块 code 而不是 id
        stmt = (
            select(Module.code)
            .join(TenantModule, Module.id == TenantModule.module_id)
            .where(
                Module.is_active == True,
                TenantModule.is_active == True,
            )
        )

        if tenant_id:
            stmt = stmt.where(TenantModule.tenant_id == tenant_id)

        result = await session.execute(stmt)
        return {row[0] for row in result.fetchall()}

    @staticmethod
    async def _get_user_permissions(
        session, user_id: str, tenant_id: str | None
    ) -> set[str]:
        """
        获取用户的所有权限 ID

        通过 UserRole -> Role -> RolePermission -> Permission 链路查询。

        Args:
            session: 数据库会话
            user_id: 用户 ID
            tenant_id: 租户 ID

        Returns:
            set[str]: 权限 ID 集合
        """
        # 构建用户权限查询
        stmt = (
            select(Permission.id)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, RolePermission.role_id == Role.id)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )

        if tenant_id:
            stmt = stmt.where(UserRole.tenant_id == tenant_id)

        result = await session.execute(stmt)
        return {row[0] for row in result.fetchall()}

    @staticmethod
    async def _get_visible_menus(
        session, tenant_id: str | None, module_ids: set[str]
    ) -> list[Menu]:
        """
        获取所有可见菜单

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            module_ids: 启用的模块 ID 集合

        Returns:
            list[Menu]: 菜单列表
        """
        # 构建菜单查询条件
        conditions = [
            Menu.is_visible == True,
            Menu.module.in_(module_ids) if module_ids else None,
        ]
        # 过滤 None 条件
        conditions = [c for c in conditions if c is not None]

        stmt = (
            select(Menu)
            .where(and_(*conditions))
            .order_by(Menu.tree_sorts)
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def _get_menu_permissions(
        session, menu_ids: list[str]
    ) -> dict[str, set[str]]:
        """
        获取菜单的权限关联

        Args:
            session: 数据库会话
            menu_ids: 菜单 ID 列表

        Returns:
            dict[str, set[str]]: menu_id -> permission_ids 映射
        """
        if not menu_ids:
            return {}

        stmt = select(MenuPermission).where(MenuPermission.menu_id.in_(menu_ids))
        result = await session.execute(stmt)
        menu_permissions = list(result.scalars().all())

        # 构建 menu_id -> permission_ids 映射
        menu_permission_map: dict[str, set[str]] = {}
        for mp in menu_permissions:
            if mp.menu_id not in menu_permission_map:
                menu_permission_map[mp.menu_id] = set()
            menu_permission_map[mp.menu_id].add(mp.permission_id)

        return menu_permission_map

    @staticmethod
    def _filter_visible_menus(
        all_menus: list[Menu],
        menu_permission_map: dict[str, set[str]],
        user_permission_ids: set[str],
    ) -> set[str]:
        """
        过滤用户有权限访问的菜单

        Args:
            all_menus: 所有菜单列表
            menu_permission_map: 菜单权限映射
            user_permission_ids: 用户权限 ID 集合

        Returns:
            set[str]: 可见菜单 ID 集合
        """
        visible_menu_ids = set()

        for menu in all_menus:
            menu_perms = menu_permission_map.get(menu.id, set())
            # 无权限限制的菜单，所有登录用户可见
            if not menu_perms:
                visible_menu_ids.add(menu.id)
            # 用户拥有任一权限即可见
            elif menu_perms & user_permission_ids:
                visible_menu_ids.add(menu.id)

        return visible_menu_ids

    @staticmethod
    def _include_parent_menus(
        all_menus: list[Menu],
        visible_menu_ids: set[str]
    ) -> set[str]:
        """
        包含父菜单

        子菜单有权限时，父菜单也需要显示（用于构建树结构）。

        Args:
            all_menus: 所有菜单列表
            visible_menu_ids: 当前可见菜单 ID 集合

        Returns:
            set[str]: 包含父菜单的可见菜单 ID 集合
        """
        # 构建 id -> menu 映射
        menu_map = {m.id: m for m in all_menus}

        # 对于每个可见菜单，添加其所有父菜单
        result_ids = set(visible_menu_ids)

        for menu_id in visible_menu_ids:
            menu = menu_map.get(menu_id)
            if not menu:
                continue

            # 遍历父菜单链
            parent_ids = menu.parent_ids
            if parent_ids:
                # parent_ids 格式为 "id1,id2,id3"，从根到父
                for parent_id in parent_ids.split(","):
                    parent_id = parent_id.strip()
                    if parent_id and parent_id != "root":
                        result_ids.add(parent_id)

        return result_ids

    @staticmethod
    def _build_menu_tree(menus: list[Menu]) -> list[MenuTreeDict]:
        """
        构建菜单树

        Args:
            menus: 菜单列表

        Returns:
            list[MenuTreeDict]: 菜单树列表
        """
        if not menus:
            return []

        # 构建 id -> menu 映射
        menu_map = {m.id: m for m in menus}

        # 构建树节点字典
        tree_map: dict[str, MenuTreeDict] = {}
        for menu in menus:
            tree_map[menu.id] = {
                "id": menu.id,
                "code": menu.code,
                "name": menu.name,
                "icon": menu.icon,
                "path": menu.path if menu.path else None,
                "sort_order": menu.tree_sort,
                "children": [],
            }

        # 构建树结构
        root_nodes: list[MenuTreeDict] = []
        for menu in menus:
            node = tree_map[menu.id]
            parent_id = menu.parent_id

            # 顶级节点或父节点不在列表中
            if not parent_id or parent_id == "root" or parent_id not in tree_map:
                root_nodes.append(node)
            else:
                # 添加到父节点的 children
                parent_node = tree_map[parent_id]
                parent_node["children"].append(node)

        # 按 sort_order 排序
        def sort_children(node: MenuTreeDict) -> None:
            node["children"].sort(key=lambda x: x["sort_order"])
            for child in node["children"]:
                sort_children(child)

        root_nodes.sort(key=lambda x: x["sort_order"])
        for node in root_nodes:
            sort_children(node)

        return root_nodes


# 服务单例
user_menu_service = UserMenuService()
