"""
模块定义同步服务

负责将模块定义（菜单、权限、角色）同步到数据库。
"""

import fnmatch

from loguru import logger
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from framework.module.definition import (
    GLOBAL_ROLES,
    MenuDef,
    ModuleDefinition,
    PermissionDef,
    RoleDef,
)
from framework.module.registry import get_registry
from framework.utils.log_util import write_error, write_info, write_warning
from tenant.models import (
    Module,
    ModuleMenu,
    ModulePermission,
    ModuleRole,
    ModuleRolePermission,
)

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
        stmt = (
            insert(Module)
            .values(
                code=definition.code,
                name=definition.name,
                description=definition.description,
                icon=definition.icon,
                version=definition.version,
                is_active=True,
                is_need=False,
            )
            .on_conflict_do_update(
                index_elements=["code"],
                set_={
                    "name": definition.name,
                    "description": definition.description,
                    "icon": definition.icon,
                    "version": definition.version,
                },
            )
            .returning(Module.id)
        )

        result = await session.execute(stmt)
        module_id = result.scalar_one()

        # 2. 同步菜单
        await self._sync_menus(
            session, module_id, definition.code, definition.menus
        )

        # 3. 同步权限
        await self._sync_permissions(
            session, module_id, definition.code, definition.permissions
        )

        # 4. 同步角色
        await self._sync_roles(
            session, module_id, definition.code, definition.default_roles
        )

        # 5. 清理孤儿数据
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
        使用两阶段处理：先创建所有菜单，再更新父子关系。

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

        # 第一阶段：创建所有菜单（不设置 parent_id）
        code_to_id_map: dict[str, str] = {}

        for menu_def in menus:
            stmt = (
                insert(ModuleMenu)
                .values(
                    module_id=module_id,
                    parent_id=None,  # 先不设置父菜单
                    code=menu_def.code,
                    name=menu_def.name,
                    path=menu_def.path,
                    icon=menu_def.icon,
                    sort_order=menu_def.sort_order,
                    is_visible=menu_def.is_visible,
                )
                .on_conflict_do_update(
                    index_elements=["code"],
                    set_={
                        "name": menu_def.name,
                        "path": menu_def.path,
                        "icon": menu_def.icon,
                        "sort_order": menu_def.sort_order,
                        "is_visible": menu_def.is_visible,
                    },
                )
                .returning(ModuleMenu.id)
            )

            result = await session.execute(stmt)
            menu_id = result.scalar_one()
            code_to_id_map[menu_def.code] = menu_id

        # 第二阶段：更新父子关系（使用 update 语句避免 N+1 问题）
        for menu_def in menus:
            if menu_def.parent_code is None:
                continue

            # 检查父菜单是否存在
            if menu_def.parent_code not in code_to_id_map:
                raise ValueError(
                    f"菜单 {menu_def.code} 的父菜单 {menu_def.parent_code} 不存在"
                )

            parent_id = code_to_id_map[menu_def.parent_code]
            menu_id = code_to_id_map[menu_def.code]

            # 使用 update 语句直接更新，避免 SELECT
            stmt = (
                update(ModuleMenu)
                .where(ModuleMenu.id == menu_id)
                .values(parent_id=parent_id)
            )
            await session.execute(stmt)

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
            stmt = (
                insert(ModulePermission)
                .values(
                    module_id=module_id,
                    code=perm_def.code,
                    name=perm_def.name,
                    resource=perm_def.resource,
                    action=perm_def.action,
                    description=perm_def.description,
                )
                .on_conflict_do_update(
                    index_elements=["code"],
                    set_={
                        "name": perm_def.name,
                        "resource": perm_def.resource,
                        "action": perm_def.action,
                        "description": perm_def.description,
                    },
                )
            )

            await session.execute(stmt)

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
        stmt = select(ModulePermission.id, ModulePermission.code).where(
            ModulePermission.module_id == module_id
        )
        result = await session.execute(stmt)
        perm_code_to_id = {row.code: row.id for row in result.all()}

        for role_def in roles:
            # Upsert 角色
            stmt = (
                insert(ModuleRole)
                .values(
                    module_id=module_id,
                    code=role_def.code,
                    name=role_def.name,
                    description=role_def.description,
                    is_system=role_def.is_system,
                )
                .on_conflict_do_update(
                    constraint="uq_module_roles_module_code",
                    set_={
                        "name": role_def.name,
                        "description": role_def.description,
                        "is_system": role_def.is_system,
                    },
                )
                .returning(ModuleRole.id)
            )

            result = await session.execute(stmt)
            role_id = result.scalar_one()

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
                stmt = delete(ModuleRolePermission).where(
                    ModuleRolePermission.module_role_id == role_id
                )
                await session.execute(stmt)

                # 创建新的权限关联（使用展开后的具体权限码）
                for perm_code in expanded_codes:
                    perm_id = perm_code_to_id[perm_code]
                    stmt = (
                        insert(ModuleRolePermission)
                        .values(
                            module_role_id=role_id,
                            module_permission_id=perm_id,
                        )
                        .on_conflict_do_nothing(
                            constraint="uq_module_role_permissions_role_perm"
                        )
                    )
                    await session.execute(stmt)

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
        # 清理孤儿菜单
        if menus:
            menu_codes = [menu.code for menu in menus]
            stmt = delete(ModuleMenu).where(
                ModuleMenu.module_id == module_id,
                ModuleMenu.code.not_in(menu_codes),
            )
            await session.execute(stmt)
        else:
            # 如果没有菜单定义，删除该模块的所有菜单
            stmt = delete(ModuleMenu).where(ModuleMenu.module_id == module_id)
            await session.execute(stmt)

        # 清理孤儿权限
        if permissions:
            perm_codes = [perm.code for perm in permissions]
            stmt = delete(ModulePermission).where(
                ModulePermission.module_id == module_id,
                ModulePermission.code.not_in(perm_codes),
            )
            await session.execute(stmt)
        else:
            stmt = delete(ModulePermission).where(
                ModulePermission.module_id == module_id
            )
            await session.execute(stmt)

        # 清理孤儿角色
        if roles:
            role_codes = [role.code for role in roles]
            # 先获取要删除的角色ID
            stmt = select(ModuleRole.id).where(
                ModuleRole.module_id == module_id,
                ModuleRole.code.not_in(role_codes),
            )
            result = await session.execute(stmt)
            role_ids_to_delete = [row.id for row in result.all()]

            if role_ids_to_delete:
                # 删除角色权限关联
                stmt = delete(ModuleRolePermission).where(
                    ModuleRolePermission.module_role_id.in_(role_ids_to_delete)
                )
                await session.execute(stmt)

                # 删除角色
                stmt = delete(ModuleRole).where(ModuleRole.id.in_(role_ids_to_delete))
                await session.execute(stmt)
        else:
            # 如果没有角色定义，删除该模块的所有角色
            stmt = select(ModuleRole.id).where(ModuleRole.module_id == module_id)
            result = await session.execute(stmt)
            role_ids = [row.id for row in result.all()]

            if role_ids:
                # 删除角色权限关联
                stmt = delete(ModuleRolePermission).where(
                    ModuleRolePermission.module_role_id.in_(role_ids)
                )
                await session.execute(stmt)

                # 删除角色
                stmt = delete(ModuleRole).where(ModuleRole.module_id == module_id)
                await session.execute(stmt)

    async def sync_global_roles(self, session: AsyncSession) -> None:
        """
        同步全局角色定义

        将全局共享角色（sysAdmin、normalUser）同步到数据库。
        全局角色的 module_id 为 NULL，权限通过通配符匹配所有模块的权限。

        Args:
            session: 数据库会话
        """
        # 1. 获取所有模块的所有权限的 code -> id 映射
        stmt = select(ModulePermission.id, ModulePermission.code)
        result = await session.execute(stmt)
        all_perm_code_to_id = {row.code: row.id for row in result.all()}

        for role_def in GLOBAL_ROLES:
            # 2. 通过 code 匹配全局角色（module_id 为 NULL）
            stmt = select(ModuleRole).where(
                ModuleRole.module_id.is_(None),
                ModuleRole.code == role_def.code,
            )
            result = await session.execute(stmt)
            existing_role = result.scalar_one_or_none()

            if existing_role:
                # 更新已有全局角色
                existing_role.name = role_def.name
                existing_role.description = role_def.description
                existing_role.is_system = role_def.is_system
                await session.flush()
                role_id = existing_role.id
            else:
                # 创建新的全局角色
                role = ModuleRole(
                    module_id=None,
                    code=role_def.code,
                    name=role_def.name,
                    description=role_def.description,
                    is_system=role_def.is_system,
                )
                session.add(role)
                await session.flush()
                role_id = role.id

            # 3. 同步角色权限关联
            if role_def.permission_codes:
                # 展开通配符权限码为具体权限码列表
                expanded_codes = _expand_permission_codes(
                    role_def.permission_codes, all_perm_code_to_id
                )

                # 删除旧的权限关联
                stmt = delete(ModuleRolePermission).where(
                    ModuleRolePermission.module_role_id == role_id
                )
                await session.execute(stmt)

                # 创建新的权限关联
                for perm_code in expanded_codes:
                    perm_id = all_perm_code_to_id.get(perm_code)
                    if not perm_id:
                        # 全局角色匹配时，某些权限可能尚未入库，跳过
                        continue
                    stmt = (
                        insert(ModuleRolePermission)
                        .values(
                            module_role_id=role_id,
                            module_permission_id=perm_id,
                        )
                        .on_conflict_do_nothing(
                            constraint="uq_module_role_permissions_role_perm"
                        )
                    )
                    await session.execute(stmt)

        # 4. 清理不再存在的全局角色
        global_role_codes = [role.code for role in GLOBAL_ROLES]
        stmt = select(ModuleRole.id).where(
            ModuleRole.module_id.is_(None),
            ModuleRole.code.not_in(global_role_codes),
        )
        result = await session.execute(stmt)
        orphan_role_ids = [row.id for row in result.all()]

        if orphan_role_ids:
            # 删除孤儿角色的权限关联
            stmt = delete(ModuleRolePermission).where(
                ModuleRolePermission.module_role_id.in_(orphan_role_ids)
            )
            await session.execute(stmt)

            # 删除孤儿角色
            stmt = delete(ModuleRole).where(ModuleRole.id.in_(orphan_role_ids))
            await session.execute(stmt)

        await session.commit()
