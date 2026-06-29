"""
模块定义同步服务

负责将模块定义（菜单、权限、角色）同步到数据库。
"""

import fnmatch

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from framework.module.definition import (
    GLOBAL_ROLES,
    MenuDef,
    ModuleDefinition,
    PermissionDef,
    RoleDef,
)
from framework.module.registry import get_registry
from framework.tenant.sync_protocols import get_module_definition_sync_provider
from framework.utils.log_util import write_error, write_info, write_warning

_logger = logger.bind(name=__name__)


def _is_wildcard(code: str) -> bool:
    """判断权限码是否包含通配符"""
    return "*" in code


def _expand_permission_codes(
    codes: list[str],
    perm_code_to_id: dict[str, str],
) -> list[str]:
    """
    展开通配符权限码为具体权限码列表

    支持的通配符模式：
    - {module}:*:* → 匹配模块下所有权限
    - {module}:*:read → 匹配模块下所有 read 权限
    - {module}:user:* → 匹配 user 资源下所有权限

    非通配符权限码原样保留。
    """
    expanded: list[str] = []
    for code in codes:
        if _is_wildcard(code):
            for perm_code in perm_code_to_id:
                if fnmatch.fnmatch(perm_code, code):
                    expanded.append(perm_code)
        else:
            expanded.append(code)
    return expanded


class ModuleDefinitionSyncService:
    """
    模块定义同步服务

    负责将模块的元数据定义（菜单、权限、角色）同步到数据库。
    在系统启动时调用，确保数据库中的定义与模块声明一致。
    """

    def __init__(self) -> None:
        self._provider = get_module_definition_sync_provider()

    async def sync_all_modules(self, session: AsyncSession) -> None:
        """
        同步所有模块的定义到数据库

        遍历所有已注册的模块，将模块定义同步到数据库。
        包括菜单、权限、角色的同步，以及孤儿数据清理。

        Args:
            session: 数据库会话
        """
        registry = get_registry()
        modules = registry.get_all_modules()

        for module in modules:
            definition = module.get_module_definition()
            if definition is None:
                write_warning(f"模块 {module.name} 无模块定义，跳过同步")
                continue

            try:
                await self.sync_module(session, definition)
                write_info(f"模块 {definition.code} 同步完成")
            except Exception as e:
                _logger.error(f"模块 {definition.code} 同步失败: {e}")
                write_error(f"模块 {definition.code} 同步失败")
                raise

        # 同步全局角色（在所有模块同步完成后，确保所有权限已入库）
        try:
            await self.sync_global_roles(session)
            write_info("全局角色同步完成")
        except Exception as e:
            _logger.error(f"全局角色同步失败: {e}")
            write_error("全局角色同步失败")
            raise

    async def sync_module(
        self, session: AsyncSession, definition: ModuleDefinition
    ) -> None:
        """
        同步单个模块定义

        将模块定义中的菜单、权限、角色同步到数据库。

        Args:
            session: 数据库会话
            definition: 模块定义实例
        """
        # 1. Upsert Module 记录
        module_id = await self._provider.upsert_module(session, definition)

        # 2. 同步菜单
        await self._sync_menus(
            session, module_id, definition.code, definition.menus
        )

        # 3. 同步权限
        await self._sync_permissions(
            session, module_id, definition.code, definition.permissions
        )

        # 4. 同步菜单权限关联
        await self._sync_menu_permissions(
            session, module_id, definition.code, definition.menus
        )

        # 5. 同步角色
        await self._sync_roles(
            session, module_id, definition.code, definition.default_roles
        )

        # 6. 清理孤儿数据
        await self._cleanup_orphans(
            session,
            module_id,
            definition.code,
            definition.menus,
            definition.permissions,
            definition.default_roles,
        )

        await session.commit()

    async def _sync_menus(
        self,
        session: AsyncSession,
        module_id: str,
        module_code: str,
        menus: list[MenuDef],
    ) -> None:
        """
        同步菜单定义

        将模块的菜单定义同步到数据库。
        使用 TreeNodeMixin 的 create_node 和 update_node 方法管理树形结构。

        Args:
            session: 数据库会话
            module_id: 模块ID
            module_code: 模块编码
            menus: 菜单定义列表

        Raises:
            ValueError: 菜单循环引用或父菜单不存在
        """
        if not menus:
            return

        # 检测循环引用
        self._detect_menu_cycles(menus)

        # 构建 code -> MenuDef 映射
        menu_def_map = {menu.code: menu for menu in menus}

        # 拓扑排序：按层级顺序创建菜单（父节点先于子节点）
        sorted_menus = self._topological_sort_menus(menus, menu_def_map)

        # 获取已存在的菜单 code -> id 映射
        existing_code_to_id = await self._provider.get_menu_code_to_id_map(
            session, module_id
        )

        # code -> id 映射（用于建立父子关系）
        code_to_id_map: dict[str, str] = {}

        for menu_def in sorted_menus:
            # 计算父菜单ID
            parent_id = None
            if menu_def.parent_code:
                if menu_def.parent_code not in code_to_id_map:
                    raise ValueError(
                        f"菜单 {menu_def.code} 的父菜单 {menu_def.parent_code} 不存在或未创建"
                    )
                parent_id = code_to_id_map[menu_def.parent_code]

            existing_menu_id = existing_code_to_id.get(menu_def.code)
            menu_id = await self._provider.upsert_menu(
                session,
                module_id,
                menu_def,
                parent_id,
                existing_menu_id,
            )
            code_to_id_map[menu_def.code] = menu_id

    def _topological_sort_menus(
        self, menus: list[MenuDef], menu_def_map: dict[str, MenuDef]
    ) -> list[MenuDef]:
        """
        对菜单进行拓扑排序，确保父节点在子节点之前创建

        Args:
            menus: 菜单定义列表
            menu_def_map: code -> MenuDef 映射

        Returns:
            排序后的菜单列表
        """
        # 计算每个菜单的层级深度
        depth_cache: dict[str, int] = {}

        def get_depth(code: str) -> int:
            if code in depth_cache:
                return depth_cache[code]

            menu = menu_def_map.get(code)
            if not menu or not menu.parent_code:
                depth_cache[code] = 0
                return 0

            # 父菜单不在当前批次，视为根层菜单
            if menu.parent_code not in menu_def_map:
                depth_cache[code] = 0
                return 0

            parent_depth = get_depth(menu.parent_code)
            depth_cache[code] = parent_depth + 1
            return depth_cache[code]

        # 按层级排序
        sorted_menus = sorted(menus, key=lambda m: get_depth(m.code))
        return sorted_menus

    def _detect_menu_cycles(self, menus: list[MenuDef]) -> None:
        """
        检测菜单循环引用

        Args:
            menus: 菜单定义列表

        Raises:
            ValueError: 存在循环引用
        """
        menu_def_map = {menu.code: menu for menu in menus}
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(code: str) -> bool:
            visited.add(code)
            rec_stack.add(code)

            menu = menu_def_map.get(code)
            if menu and menu.parent_code:
                # 父菜单不存在于当前批次，跳过检测（由 _sync_menus 处理）
                if menu.parent_code not in menu_def_map:
                    rec_stack.remove(code)
                    return False
                if menu.parent_code not in visited:
                    if has_cycle(menu.parent_code):
                        return True
                elif menu.parent_code in rec_stack:
                    return True

            rec_stack.remove(code)
            return False

        for menu in menus:
            if menu.code not in visited:
                if has_cycle(menu.code):
                    raise ValueError(f"检测到菜单循环引用，涉及菜单: {menu.code}")

    async def _sync_permissions(
        self,
        session: AsyncSession,
        module_id: str,
        module_code: str,
        permissions: list[PermissionDef],
    ) -> None:
        """
        同步权限定义

        将模块的权限定义同步到数据库。

        Args:
            session: 数据库会话
            module_id: 模块ID
            module_code: 模块编码
            permissions: 权限定义列表
        """
        if not permissions:
            return

        for perm_def in permissions:
            await self._provider.upsert_permission(
                session, module_id, perm_def
            )

    async def _sync_menu_permissions(
        self,
        session: AsyncSession,
        module_id: str,
        module_code: str,
        menus: list[MenuDef],
    ) -> None:
        """
        同步菜单权限关联

        将菜单定义中的权限关联同步到数据库。

        Args:
            session: 数据库会话
            module_id: 模块ID
            module_code: 模块编码
            menus: 菜单定义列表

        Raises:
            ValueError: 菜单引用的权限不存在
        """
        # 过滤出有权限定义的菜单
        menus_with_perms = [m for m in menus if m.permission_codes]
        if not menus_with_perms:
            return

        # 获取模块所有菜单和权限的 code -> id 映射
        menu_code_to_id = await self._provider.get_menu_code_to_id_map(
            session, module_id
        )
        perm_code_to_id = await self._provider.get_permission_code_to_id_map(
            session, module_id
        )

        for menu_def in menus_with_perms:
            menu_id = menu_code_to_id.get(menu_def.code)
            if not menu_id:
                continue

            # 展开通配符权限码
            expanded_codes = _expand_permission_codes(
                menu_def.permission_codes, perm_code_to_id
            )

            # 验证非通配符权限是否存在
            missing_perms = [
                code
                for code in menu_def.permission_codes
                if not _is_wildcard(code) and code not in perm_code_to_id
            ]
            if missing_perms:
                raise ValueError(
                    f"菜单 {menu_def.code} 引用的权限不存在: {missing_perms}"
                )

            # 删除旧的菜单权限关联
            await self._provider.delete_menu_permissions(session, menu_id)

            # 创建新的菜单权限关联
            for perm_code in expanded_codes:
                perm_id = perm_code_to_id.get(perm_code)
                if not perm_id:
                    continue

                await self._provider.upsert_menu_permission(
                    session, menu_id, perm_id
                )

    async def _sync_roles(
        self,
        session: AsyncSession,
        module_id: str,
        module_code: str,
        roles: list[RoleDef],
    ) -> None:
        """
        同步角色定义

        将模块的默认角色定义同步到数据库。

        Args:
            session: 数据库会话
            module_id: 模块ID
            module_code: 模块编码
            roles: 角色定义列表

        Raises:
            ValueError: 角色权限 code 不存在
        """
        if not roles:
            return

        # 获取模块所有权限的 code -> id 映射
        perm_code_to_id = await self._provider.get_permission_code_to_id_map(
            session, module_id
        )

        for role_def in roles:
            # Upsert 角色
            role_id = await self._provider.upsert_role(
                session, role_def, module_id
            )

            # 同步角色权限关联
            if role_def.permission_codes:
                # 展开通配符权限码为具体权限码列表
                expanded_codes = _expand_permission_codes(
                    role_def.permission_codes, perm_code_to_id
                )

                # 验证非通配符权限是否存在
                missing_perms = [
                    code
                    for code in role_def.permission_codes
                    if not _is_wildcard(code) and code not in perm_code_to_id
                ]
                if missing_perms:
                    raise ValueError(
                        f"角色 {role_def.code} 引用的权限不存在: {missing_perms}"
                    )

                # 删除旧的权限关联
                await self._provider.delete_role_permissions(session, role_id)

                # 创建新的权限关联（使用展开后的具体权限码）
                for perm_code in expanded_codes:
                    perm_id = perm_code_to_id[perm_code]
                    await self._provider.upsert_role_permission(
                        session, role_id, perm_id
                    )

    async def _cleanup_orphans(
        self,
        session: AsyncSession,
        module_id: str,
        module_code: str,
        menus: list[MenuDef],
        permissions: list[PermissionDef],
        roles: list[RoleDef],
    ) -> None:
        """
        清理孤儿数据

        删除数据库中已不存在于模块定义的菜单、权限、角色。

        Args:
            session: 数据库会话
            module_id: 模块ID
            module_code: 模块编码
            menus: 菜单定义列表
            permissions: 权限定义列表
            roles: 角色定义列表
        """
        await self._provider.cleanup_orphans(
            session, module_id, menus, permissions, roles
        )

    async def sync_global_roles(self, session: AsyncSession) -> None:
        """
        同步全局角色定义

        将全局共享角色（sysAdmin、normalUser）同步到数据库。
        全局角色的 module_id 为 NULL，权限通过通配符匹配所有模块的权限。

        Args:
            session: 数据库会话
        """
        # 1. 获取所有模块的所有权限的 code -> id 映射
        all_perm_code_to_id = await self._provider.get_all_permission_code_to_id_map(
            session
        )

        for role_def in GLOBAL_ROLES:
            # 2. Upsert 全局角色
            role_id = await self._provider.upsert_global_role(session, role_def)

            # 3. 同步角色权限关联
            if role_def.permission_codes:
                # 展开通配符权限码为具体权限码列表
                expanded_codes = _expand_permission_codes(
                    role_def.permission_codes, all_perm_code_to_id
                )

                # 删除旧的权限关联
                await self._provider.delete_role_permissions(session, role_id)

                # 创建新的权限关联
                for perm_code in expanded_codes:
                    perm_id = all_perm_code_to_id.get(perm_code)
                    if not perm_id:
                        # 全局角色匹配时，某些权限可能尚未入库，跳过
                        continue
                    await self._provider.upsert_role_permission(
                        session, role_id, perm_id
                    )

        # 4. 清理不再存在的全局角色
        global_role_codes = [role.code for role in GLOBAL_ROLES]
        await self._provider.delete_orphan_global_roles(session, global_role_codes)

        await session.commit()
