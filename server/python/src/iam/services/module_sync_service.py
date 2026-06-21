"""
模块同步服务

监听 Tenant 模块的事件，同步模块定义层数据到租户实例层。
"""

import logging
from collections import defaultdict

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import Menu, MenuPermission, Permission, Role, RolePermission
from iam.services.permission_service import PermissionCheckService

_logger = logging.getLogger(__name__)


class ModuleSyncService:
    """模块同步服务"""

    @staticmethod
    async def sync_module_assigned(
        session: AsyncSession,
        tenant_id: str,
        module_id: str,
        module_code: str,
    ) -> None:
        """
        同步模块分配事件

        当租户分配模块时，创建租户实例层的菜单、权限、角色数据。

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            module_id: 模块 ID
            module_code: 模块编码
        """
        _logger.info(f"开始同步模块分配: tenant_id={tenant_id}, module={module_code}")

        # 导入模块定义层模型
        from tenant.models import (
            ModuleMenu,
            ModuleMenuPermission,
            ModulePermission,
            ModuleRole,
            ModuleRolePermission,
        )

        # 1. 查询模块的所有菜单
        menu_stmt = select(ModuleMenu).where(ModuleMenu.module_id == module_id)
        menu_result = await session.execute(menu_stmt)
        module_menus = list(menu_result.scalars().all())

        # 2. 查询模块的所有权限
        perm_stmt = select(ModulePermission).where(
            ModulePermission.module_id == module_id
        )
        perm_result = await session.execute(perm_stmt)
        module_permissions = list(perm_result.scalars().all())

        # 3. 查询模块的所有角色及其权限关联
        role_stmt = select(ModuleRole).where(ModuleRole.module_id == module_id)
        role_result = await session.execute(role_stmt)
        module_roles = list(role_result.scalars().all())

        role_ids = [r.id for r in module_roles]
        role_perm_stmt = select(ModuleRolePermission).where(
            ModuleRolePermission.module_role_id.in_(role_ids)
        )
        role_perm_result = await session.execute(role_perm_stmt)
        module_role_permissions = list(role_perm_result.scalars().all())

        # 构建角色 ID -> 权限 ID 列表映射
        role_perms_map: dict[str, list[str]] = defaultdict(list)
        for mrp in module_role_permissions:
            role_perms_map[mrp.module_role_id].append(mrp.module_permission_id)

        # 查询模块菜单权限关联
        menu_perm_stmt = select(ModuleMenuPermission).where(
            ModuleMenuPermission.module_menu_id.in_([m.id for m in module_menus])
        )
        menu_perm_result = await session.execute(menu_perm_stmt)
        module_menu_permissions = list(menu_perm_result.scalars().all())

        # 4. 创建租户实例层的菜单（先处理 parent_id 映射）
        menu_id_map: dict[str, str] = {}  # module_menu_id -> tenant_menu_id

        # 查询已存在的菜单（幂等检查：优先通过 ref_id，其次通过 tenant_id + module + code）
        if module_menus:
            existing_menu_stmt = select(Menu).where(
                Menu.tenant_id == tenant_id,
                Menu.module == module_code,
            )
            existing_menu_result = await session.execute(existing_menu_stmt)
            # 同时建立 ref_id 映射和 code 映射，兼容有无 ref_id 的历史数据
            existing_menus_by_ref: dict[str, Menu] = {}
            existing_menus_by_code: dict[str, Menu] = {}
            for m in existing_menu_result.scalars().all():
                if m.ref_id:
                    existing_menus_by_ref[m.ref_id] = m
                existing_menus_by_code[m.code] = m
        else:
            existing_menus_by_ref = {}
            existing_menus_by_code = {}

        # 按树层级排序，确保父菜单先创建
        sorted_menus = sorted(module_menus, key=lambda m: m.parent_id or "")

        for mm in sorted_menus:
            # 幂等检查：优先通过 ref_id，其次通过 code
            existing = existing_menus_by_ref.get(mm.id) or existing_menus_by_code.get(
                mm.code
            )
            if existing:
                menu_id_map[mm.id] = existing.id
                # 如果历史数据缺少 ref_id，补全它
                if not existing.ref_id:
                    existing.ref_id = mm.id
                    await session.flush()
                continue

            # 查找父菜单的租户 ID
            tenant_parent_id = None
            if mm.parent_id:
                tenant_parent_id = menu_id_map.get(mm.parent_id)

            # 使用 Menu.create_node() 创建菜单，自动维护树形字段
            # 将 sort_order 映射到 tree_sort
            menu = await Menu.create_node(
                session,
                {
                    "tenant_id": tenant_id,
                    "parent_id": tenant_parent_id or None,
                    "module": module_code,
                    "code": mm.code,
                    "name": mm.name,
                    "path": mm.path,
                    "icon": mm.icon,
                    "is_visible": mm.is_visible,
                    "ref_id": mm.id,
                    "tree_sort": mm.sort_order,  # 映射 sort_order -> tree_sort
                },
            )
            menu_id_map[mm.id] = menu.id

        # 5. 创建租户实例层的权限
        perm_id_map: dict[str, str] = {}  # module_permission_id -> tenant_permission_id

        # 查询已存在的权限（幂等检查：优先通过 ref_id，其次通过 tenant_id + code）
        if module_permissions:
            existing_perm_stmt = select(Permission).where(
                Permission.tenant_id == tenant_id,
            )
            existing_perm_result = await session.execute(existing_perm_stmt)
            existing_perms_by_ref: dict[str, Permission] = {}
            existing_perms_by_code: dict[str, Permission] = {}
            for p in existing_perm_result.scalars().all():
                if p.ref_id:
                    existing_perms_by_ref[p.ref_id] = p
                existing_perms_by_code[p.code] = p
        else:
            existing_perms_by_ref = {}
            existing_perms_by_code = {}

        for mp in module_permissions:
            # 幂等检查：优先通过 ref_id，其次通过 code
            existing = existing_perms_by_ref.get(mp.id) or existing_perms_by_code.get(
                mp.code
            )
            if existing:
                perm_id_map[mp.id] = existing.id
                # 如果历史数据缺少 ref_id，补全它
                if not existing.ref_id:
                    existing.ref_id = mp.id
                    await session.flush()
                continue

            permission = Permission(
                tenant_id=tenant_id,
                code=mp.code,
                name=mp.name,
                resource=mp.resource,
                action=mp.action,
                description=mp.description,
                ref_id=mp.id,
            )
            session.add(permission)
            await session.flush()
            perm_id_map[mp.id] = permission.id

        # 6. 创建租户实例层的角色
        role_id_map: dict[str, str] = {}  # module_role_id -> tenant_role_id

        # 查询已存在的角色（幂等检查：优先通过 ref_id，其次通过 tenant_id + code）
        if module_roles:
            existing_role_stmt = select(Role).where(
                Role.tenant_id == tenant_id,
            )
            existing_role_result = await session.execute(existing_role_stmt)
            existing_roles_by_ref: dict[str, Role] = {}
            existing_roles_by_code: dict[str, Role] = {}
            for r in existing_role_result.scalars().all():
                if r.ref_id:
                    existing_roles_by_ref[r.ref_id] = r
                existing_roles_by_code[r.code] = r
        else:
            existing_roles_by_ref = {}
            existing_roles_by_code = {}

        for mr in module_roles:
            # 幂等检查：优先通过 ref_id，其次通过 code
            existing = existing_roles_by_ref.get(mr.id) or existing_roles_by_code.get(
                mr.code
            )
            if existing:
                role_id_map[mr.id] = existing.id
                # 如果历史数据缺少 ref_id，补全它
                if not existing.ref_id:
                    existing.ref_id = mr.id
                    await session.flush()
                continue

            role = Role(
                tenant_id=tenant_id,
                code=mr.code,
                name=mr.name,
                description=mr.description,
                is_system=mr.is_system,
                ref_id=mr.id,
            )
            session.add(role)
            await session.flush()
            role_id_map[mr.id] = role.id

        # 7. 创建租户实例层的角色权限关联
        # 查询已存在的角色权限关联（幂等检查）
        tenant_role_ids = list(role_id_map.values())
        if tenant_role_ids:
            existing_rp_stmt = select(RolePermission).where(
                RolePermission.tenant_id == tenant_id,
                RolePermission.role_id.in_(tenant_role_ids),
            )
            existing_rp_result = await session.execute(existing_rp_stmt)
            existing_rps = {
                (rp.role_id, rp.permission_id)
                for rp in existing_rp_result.scalars().all()
            }
        else:
            existing_rps = set()

        for module_role_id, module_perm_ids in role_perms_map.items():
            tenant_role_id = role_id_map.get(module_role_id)
            if not tenant_role_id:
                continue

            for module_perm_id in module_perm_ids:
                tenant_perm_id = perm_id_map.get(module_perm_id)
                if not tenant_perm_id:
                    continue

                # 幂等检查：如果已存在则跳过
                if (tenant_role_id, tenant_perm_id) in existing_rps:
                    continue

                role_permission = RolePermission(
                    tenant_id=tenant_id,
                    role_id=tenant_role_id,
                    permission_id=tenant_perm_id,
                )
                session.add(role_permission)

        # 8. 同步全局角色到租户实例层
        await ModuleSyncService._sync_global_roles_to_tenant(
            session,
            tenant_id,
            module_id,
            perm_id_map,
        )

        # 9. 创建租户实例层的菜单权限关联
        for mmp in module_menu_permissions:
            tenant_menu_id = menu_id_map.get(mmp.module_menu_id)
            tenant_perm_id = perm_id_map.get(mmp.module_permission_id)

            if not tenant_menu_id or not tenant_perm_id:
                continue

            # 幂等检查
            existing_mp_stmt = select(MenuPermission).where(
                MenuPermission.menu_id == tenant_menu_id,
                MenuPermission.permission_id == tenant_perm_id,
            )
            mp_result = await session.execute(existing_mp_stmt)
            if mp_result.scalar_one_or_none():
                continue

            menu_permission = MenuPermission(
                menu_id=tenant_menu_id,
                permission_id=tenant_perm_id,
            )
            session.add(menu_permission)

        _logger.info(
            f"模块分配同步完成: tenant_id={tenant_id}, module={module_code}, "
            f"menus={len(module_menus)}, permissions={len(module_permissions)}, "
            f"roles={len(module_roles)}, menu_permissions={len(module_menu_permissions)}"
        )

    @staticmethod
    async def sync_module_unassigned(
        session: AsyncSession,
        tenant_id: str,
        module_id: str,
    ) -> None:
        """
        同步模块取消分配事件

        当租户取消模块分配时，删除租户实例层的菜单、权限、角色数据。
        按依赖顺序删除：RolePermission -> Role -> Permission -> Menu

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            module_id: 模块 ID
        """
        _logger.info(
            f"开始同步模块取消分配: tenant_id={tenant_id}, module_id={module_id}"
        )

        # 导入模块定义层模型
        from tenant.models import ModuleMenu, ModulePermission, ModuleRole

        # 1. 获取该模块的所有角色 ID
        role_stmt = select(ModuleRole.id).where(ModuleRole.module_id == module_id)
        role_result = await session.execute(role_stmt)
        module_role_ids = [row[0] for row in role_result.all()]

        # 2. 获取该模块的所有权限 ID
        perm_stmt = select(ModulePermission.id).where(
            ModulePermission.module_id == module_id
        )
        perm_result = await session.execute(perm_stmt)
        module_perm_ids = [row[0] for row in perm_result.all()]

        # 3. 获取该模块的所有菜单 ID
        menu_stmt = select(ModuleMenu.id).where(ModuleMenu.module_id == module_id)
        menu_result = await session.execute(menu_stmt)
        module_menu_ids = [row[0] for row in menu_result.all()]

        # 4. 查找租户实例层对应的角色（通过 ref_id）
        tenant_role_stmt = select(Role.id).where(
            Role.tenant_id == tenant_id,
            Role.ref_id.in_(module_role_ids),
        )
        tenant_role_result = await session.execute(tenant_role_stmt)
        tenant_role_ids = [row[0] for row in tenant_role_result.all()]

        # 5. 查找租户实例层对应的权限（通过 ref_id）
        tenant_perm_stmt = select(Permission.id).where(
            Permission.tenant_id == tenant_id,
            Permission.ref_id.in_(module_perm_ids),
        )
        tenant_perm_result = await session.execute(tenant_perm_stmt)
        tenant_perm_ids = [row[0] for row in tenant_perm_result.all()]

        # 6. 查找租户实例层对应的菜单（通过 ref_id）
        tenant_menu_stmt = select(Menu.id).where(
            Menu.tenant_id == tenant_id,
            Menu.ref_id.in_(module_menu_ids),
        )
        tenant_menu_result = await session.execute(tenant_menu_stmt)
        tenant_menu_ids = [row[0] for row in tenant_menu_result.all()]

        # 7. 按依赖顺序删除
        # 删除 RolePermission
        if tenant_role_ids:
            await session.execute(
                delete(RolePermission).where(
                    RolePermission.tenant_id == tenant_id,
                    RolePermission.role_id.in_(tenant_role_ids),
                )
            )
            _logger.info(f"删除租户角色权限关联: {len(tenant_role_ids)} 个角色")

        # 删除 Role
        if tenant_role_ids:
            await session.execute(
                delete(Role).where(
                    Role.tenant_id == tenant_id,
                    Role.id.in_(tenant_role_ids),
                )
            )
            _logger.info(f"删除租户角色: {len(tenant_role_ids)} 个")

        # 删除 Permission
        if tenant_perm_ids:
            await session.execute(
                delete(Permission).where(
                    Permission.tenant_id == tenant_id,
                    Permission.id.in_(tenant_perm_ids),
                )
            )
            _logger.info(f"删除租户权限: {len(tenant_perm_ids)} 个")

        # 删除 Menu（含子菜单，通过 parent_ids 查询）
        if tenant_menu_ids:
            # 先删除这些菜单的所有子菜单
            for menu_id in tenant_menu_ids:
                # 查询子菜单
                child_stmt = select(Menu.id).where(
                    Menu.tenant_id == tenant_id,
                    Menu.parent_ids.like(f"%,{menu_id},%"),
                )
                child_result = await session.execute(child_stmt)
                child_ids = [row[0] for row in child_result.all()]
                if child_ids:
                    await session.execute(delete(Menu).where(Menu.id.in_(child_ids)))

            # 删除菜单本身
            await session.execute(
                delete(Menu).where(
                    Menu.tenant_id == tenant_id,
                    Menu.id.in_(tenant_menu_ids),
                )
            )
            _logger.info(f"删除租户菜单: {len(tenant_menu_ids)} 个")

        _logger.info(f"模块取消分配同步完成: tenant_id={tenant_id}")

    @staticmethod
    async def _sync_global_roles_to_tenant(
        session: AsyncSession,
        tenant_id: str,
        module_id: str,
        perm_id_map: dict[str, str],
    ) -> None:
        """
        同步全局角色到租户实例层

        当租户分配模块时，确保全局角色（sysAdmin、normalUser）在租户实例层存在，
        并关联当前模块的权限到这些全局角色。

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            module_id: 模块 ID
            perm_id_map: 模块权限 ID -> 租户权限 ID 的映射
        """
        from tenant.models import ModuleRole, ModuleRolePermission

        # 1. 查询全局角色（module_id 为 NULL）
        global_role_stmt = select(ModuleRole).where(ModuleRole.module_id.is_(None))
        global_role_result = await session.execute(global_role_stmt)
        global_roles = list(global_role_result.scalars().all())

        if not global_roles:
            return

        # 2. 查询全局角色的权限关联
        global_role_ids = [r.id for r in global_roles]
        global_rp_stmt = select(ModuleRolePermission).where(
            ModuleRolePermission.module_role_id.in_(global_role_ids)
        )
        global_rp_result = await session.execute(global_rp_stmt)
        global_role_permissions = list(global_rp_result.scalars().all())

        # 构建全局角色 ID -> 模块权限 ID 列表映射
        global_role_perms_map: dict[str, list[str]] = defaultdict(list)
        for mrp in global_role_permissions:
            global_role_perms_map[mrp.module_role_id].append(
                mrp.module_permission_id
            )

        # 3. 查询已存在的租户角色（用于幂等检查）
        existing_role_stmt = select(Role).where(Role.tenant_id == tenant_id)
        existing_role_result = await session.execute(existing_role_stmt)
        existing_roles_by_code: dict[str, Role] = {}
        for r in existing_role_result.scalars().all():
            existing_roles_by_code[r.code] = r

        # 4. 为每个全局角色创建或更新租户实例层的角色和权限关联
        for global_role in global_roles:
            # 通过 code 匹配全局角色
            tenant_role = existing_roles_by_code.get(global_role.code)

            if not tenant_role:
                # 创建租户实例层的全局角色
                tenant_role = Role(
                    tenant_id=tenant_id,
                    code=global_role.code,
                    name=global_role.name,
                    description=global_role.description,
                    is_system=global_role.is_system,
                    ref_id=global_role.id,
                )
                session.add(tenant_role)
                await session.flush()
                # 更新映射，避免后续全局角色重复创建
                existing_roles_by_code[global_role.code] = tenant_role
            else:
                # 如果历史数据缺少 ref_id，补全它
                if not tenant_role.ref_id:
                    tenant_role.ref_id = global_role.id
                    await session.flush()

            # 5. 为全局角色关联当前模块的权限
            module_perm_ids_for_role = global_role_perms_map.get(global_role.id, [])
            if not module_perm_ids_for_role:
                continue

            # 查询已存在的角色权限关联
            existing_rp_stmt = select(RolePermission).where(
                RolePermission.tenant_id == tenant_id,
                RolePermission.role_id == tenant_role.id,
            )
            existing_rp_result = await session.execute(existing_rp_stmt)
            existing_rps = {
                (rp.role_id, rp.permission_id)
                for rp in existing_rp_result.scalars().all()
            }

            # 添加新的权限关联（仅关联当前模块的权限）
            for module_perm_id in module_perm_ids_for_role:
                tenant_perm_id = perm_id_map.get(module_perm_id)
                if not tenant_perm_id:
                    continue

                # 幂等检查
                if (tenant_role.id, tenant_perm_id) in existing_rps:
                    continue

                role_permission = RolePermission(
                    tenant_id=tenant_id,
                    role_id=tenant_role.id,
                    permission_id=tenant_perm_id,
                )
                session.add(role_permission)

        _logger.info(
            f"全局角色同步完成: tenant_id={tenant_id}, module_id={module_id}, "
            f"global_roles={len(global_roles)}"
        )

    @staticmethod
    async def sync_module_menu_created(
        session: AsyncSession,
        module_menu_id: str,
        module_id: str,
    ) -> None:
        """
        同步模块菜单创建事件

        为所有已分配该模块的租户创建菜单。

        Args:
            session: 数据库会话
            module_menu_id: 模块菜单 ID
            module_id: 模块 ID
        """
        from tenant.models import Module, ModuleMenu, TenantModule

        # 1. 获取模块信息
        module_stmt = select(Module).where(Module.id == module_id)
        module_result = await session.execute(module_stmt)
        module = module_result.scalar_one_or_none()
        if not module:
            _logger.warning(f"模块不存在: {module_id}")
            return

        # 2. 获取模块菜单信息
        menu_stmt = select(ModuleMenu).where(ModuleMenu.id == module_menu_id)
        menu_result = await session.execute(menu_stmt)
        module_menu = menu_result.scalar_one_or_none()
        if not module_menu:
            _logger.warning(f"模块菜单不存在: {module_menu_id}")
            return

        # 3. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 4. 为每个租户创建菜单
        for tenant_id in tenant_ids:
            # 查找父菜单的租户 ID
            tenant_parent_id = None
            if module_menu.parent_id:
                # 查找模块父菜单对应的租户菜单
                parent_stmt = select(Menu.id).where(
                    Menu.tenant_id == tenant_id,
                    Menu.ref_id == module_menu.parent_id,
                )
                parent_result = await session.execute(parent_stmt)
                tenant_parent_id = parent_result.scalar_one_or_none()

            # 使用 Menu.create_node() 创建菜单，自动维护树形字段
            menu = await Menu.create_node(
                session,
                {
                    "tenant_id": tenant_id,
                    "parent_id": tenant_parent_id or None,
                    "module": module.code,
                    "code": module_menu.code,
                    "name": module_menu.name,
                    "path": module_menu.path,
                    "icon": module_menu.icon,
                    "is_visible": module_menu.is_visible,
                    "ref_id": module_menu.id,
                    "tree_sort": module_menu.sort_order,  # 映射 sort_order -> tree_sort
                },
            )

        _logger.info(
            f"模块菜单创建同步完成: menu={module_menu.code}, tenants={len(tenant_ids)}"
        )

    @staticmethod
    async def sync_module_menu_updated(
        session: AsyncSession,
        module_menu_id: str,
        module_id: str,
    ) -> None:
        """
        同步模块菜单更新事件

        更新所有已分配该模块的租户的菜单。

        Args:
            session: 数据库会话
            module_menu_id: 模块菜单 ID
            module_id: 模块 ID
        """
        from tenant.models import ModuleMenu, TenantModule

        # 1. 获取模块菜单信息
        menu_stmt = select(ModuleMenu).where(ModuleMenu.id == module_menu_id)
        menu_result = await session.execute(menu_stmt)
        module_menu = menu_result.scalar_one_or_none()
        if not module_menu:
            _logger.warning(f"模块菜单不存在: {module_menu_id}")
            return

        # 2. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 3. 更新每个租户的菜单
        for tenant_id in tenant_ids:
            # 查找租户菜单
            tenant_menu_stmt = select(Menu).where(
                Menu.tenant_id == tenant_id,
                Menu.ref_id == module_menu_id,
            )
            tenant_menu_result = await session.execute(tenant_menu_stmt)
            tenant_menu = tenant_menu_result.scalar_one_or_none()

            if tenant_menu:
                # 使用 Menu.update_node() 更新菜单，自动维护树形字段
                await Menu.update_node(
                    session,
                    tenant_menu.id,
                    {
                        "name": module_menu.name,
                        "path": module_menu.path,
                        "icon": module_menu.icon,
                        "is_visible": module_menu.is_visible,
                        "tree_sort": module_menu.sort_order,  # 映射 sort_order -> tree_sort
                        "parent_id": None,  # 临时值，下面会根据 parent_id 更新
                    },
                )

                # 更新父菜单（如果变化）
                if module_menu.parent_id:
                    parent_stmt = select(Menu.id).where(
                        Menu.tenant_id == tenant_id,
                        Menu.ref_id == module_menu.parent_id,
                    )
                    parent_result = await session.execute(parent_stmt)
                    tenant_parent_id = parent_result.scalar_one_or_none()
                    if tenant_parent_id and tenant_parent_id != tenant_menu.parent_id:
                        # 再次调用 update_node 更新 parent_id
                        await Menu.update_node(
                            session,
                            tenant_menu.id,
                            {"parent_id": tenant_parent_id},
                        )

        _logger.info(
            f"模块菜单更新同步完成: menu={module_menu.code}, tenants={len(tenant_ids)}"
        )

    @staticmethod
    async def sync_module_menu_deleted(
        session: AsyncSession,
        module_id: str,
        menu_code: str,
    ) -> None:
        """
        同步模块菜单删除事件

        删除所有已分配该模块的租户的菜单。

        Args:
            session: 数据库会话
            module_id: 模块 ID
            menu_code: 菜单编码
        """
        from tenant.models import TenantModule

        # 1. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 2. 删除每个租户的菜单
        deleted_count = 0
        for tenant_id in tenant_ids:
            # 查找租户菜单
            menu_stmt = select(Menu).where(
                Menu.tenant_id == tenant_id,
                Menu.code == menu_code,
            )
            menu_result = await session.execute(menu_stmt)
            tenant_menu = menu_result.scalar_one_or_none()

            if tenant_menu:
                # 先删除子菜单
                child_stmt = select(Menu.id).where(
                    Menu.tenant_id == tenant_id,
                    Menu.parent_ids.like(f"%,{tenant_menu.id},%"),
                )
                child_result = await session.execute(child_stmt)
                child_ids = [row[0] for row in child_result.all()]
                if child_ids:
                    await session.execute(delete(Menu).where(Menu.id.in_(child_ids)))

                # 删除菜单本身
                await session.delete(tenant_menu)
                deleted_count += 1

        _logger.info(f"模块菜单删除同步完成: menu={menu_code}, tenants={deleted_count}")

    @staticmethod
    async def sync_module_permission_created(
        session: AsyncSession,
        module_permission_id: str,
        module_id: str,
    ) -> None:
        """
        同步模块权限创建事件

        为所有已分配该模块的租户创建权限。

        Args:
            session: 数据库会话
            module_permission_id: 模块权限 ID
            module_id: 模块 ID
        """
        from tenant.models import ModulePermission, TenantModule

        # 1. 获取模块权限信息
        perm_stmt = select(ModulePermission).where(
            ModulePermission.id == module_permission_id
        )
        perm_result = await session.execute(perm_stmt)
        module_perm = perm_result.scalar_one_or_none()
        if not module_perm:
            _logger.warning(f"模块权限不存在: {module_permission_id}")
            return

        # 2. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 3. 为每个租户创建权限
        for tenant_id in tenant_ids:
            permission = Permission(
                tenant_id=tenant_id,
                code=module_perm.code,
                name=module_perm.name,
                resource=module_perm.resource,
                action=module_perm.action,
                description=module_perm.description,
                ref_id=module_perm.id,
            )
            session.add(permission)

        _logger.info(
            f"模块权限创建同步完成: permission={module_perm.code}, tenants={len(tenant_ids)}"
        )

    @staticmethod
    async def sync_module_permission_updated(
        session: AsyncSession,
        module_permission_id: str,
        module_id: str,
    ) -> None:
        """
        同步模块权限更新事件

        更新所有已分配该模块的租户的权限。

        Args:
            session: 数据库会话
            module_permission_id: 模块权限 ID
            module_id: 模块 ID
        """
        from tenant.models import ModulePermission, TenantModule

        # 1. 获取模块权限信息
        perm_stmt = select(ModulePermission).where(
            ModulePermission.id == module_permission_id
        )
        perm_result = await session.execute(perm_stmt)
        module_perm = perm_result.scalar_one_or_none()
        if not module_perm:
            _logger.warning(f"模块权限不存在: {module_permission_id}")
            return

        # 2. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 3. 更新每个租户的权限
        for tenant_id in tenant_ids:
            # 查找租户权限
            tenant_perm_stmt = select(Permission).where(
                Permission.tenant_id == tenant_id,
                Permission.ref_id == module_permission_id,
            )
            tenant_perm_result = await session.execute(tenant_perm_stmt)
            tenant_perm = tenant_perm_result.scalar_one_or_none()

            if tenant_perm:
                tenant_perm.name = module_perm.name
                tenant_perm.resource = module_perm.resource
                tenant_perm.action = module_perm.action
                tenant_perm.description = module_perm.description

        _logger.info(
            f"模块权限更新同步完成: permission={module_perm.code}, tenants={len(tenant_ids)}"
        )

    @staticmethod
    async def sync_module_permission_deleted(
        session: AsyncSession,
        module_id: str,
        permission_code: str,
    ) -> None:
        """
        同步模块权限删除事件

        删除所有已分配该模块的租户的权限。

        Args:
            session: 数据库会话
            module_id: 模块 ID
            permission_code: 权限编码
        """
        from tenant.models import TenantModule

        # 1. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 2. 删除每个租户的权限
        deleted_count = 0
        for tenant_id in tenant_ids:
            # 先删除角色权限关联
            perm_stmt = select(Permission.id).where(
                Permission.tenant_id == tenant_id,
                Permission.code == permission_code,
            )
            perm_result = await session.execute(perm_stmt)
            perm_id = perm_result.scalar_one_or_none()

            if perm_id:
                # 删除角色权限关联
                await session.execute(
                    delete(RolePermission).where(
                        RolePermission.tenant_id == tenant_id,
                        RolePermission.permission_id == perm_id,
                    )
                )

                # 删除权限
                await session.execute(
                    delete(Permission).where(Permission.id == perm_id)
                )
                deleted_count += 1

        _logger.info(
            f"模块权限删除同步完成: permission={permission_code}, tenants={deleted_count}"
        )

    @staticmethod
    async def sync_module_role_created(
        session: AsyncSession,
        module_role_id: str,
        module_id: str,
    ) -> None:
        """
        同步模块角色创建事件

        为所有已分配该模块的租户创建角色。

        Args:
            session: 数据库会话
            module_role_id: 模块角色 ID
            module_id: 模块 ID
        """
        from tenant.models import ModuleRole, TenantModule

        # 1. 获取模块角色信息
        role_stmt = select(ModuleRole).where(ModuleRole.id == module_role_id)
        role_result = await session.execute(role_stmt)
        module_role = role_result.scalar_one_or_none()
        if not module_role:
            _logger.warning(f"模块角色不存在: {module_role_id}")
            return

        # 2. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 3. 为每个租户创建角色
        for tenant_id in tenant_ids:
            role = Role(
                tenant_id=tenant_id,
                code=module_role.code,
                name=module_role.name,
                description=module_role.description,
                is_system=module_role.is_system,
                ref_id=module_role.id,
            )
            session.add(role)

        _logger.info(
            f"模块角色创建同步完成: role={module_role.code}, tenants={len(tenant_ids)}"
        )

    @staticmethod
    async def sync_module_role_updated(
        session: AsyncSession,
        module_role_id: str,
        module_id: str,
    ) -> None:
        """
        同步模块角色更新事件

        更新所有已分配该模块的租户的角色。

        Args:
            session: 数据库会话
            module_role_id: 模块角色 ID
            module_id: 模块 ID
        """
        from tenant.models import ModuleRole, TenantModule

        # 1. 获取模块角色信息
        role_stmt = select(ModuleRole).where(ModuleRole.id == module_role_id)
        role_result = await session.execute(role_stmt)
        module_role = role_result.scalar_one_or_none()
        if not module_role:
            _logger.warning(f"模块角色不存在: {module_role_id}")
            return

        # 2. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 3. 更新每个租户的角色
        for tenant_id in tenant_ids:
            # 查找租户角色
            tenant_role_stmt = select(Role).where(
                Role.tenant_id == tenant_id,
                Role.ref_id == module_role_id,
            )
            tenant_role_result = await session.execute(tenant_role_stmt)
            tenant_role = tenant_role_result.scalar_one_or_none()

            if tenant_role:
                tenant_role.name = module_role.name
                tenant_role.description = module_role.description

        _logger.info(
            f"模块角色更新同步完成: role={module_role.code}, tenants={len(tenant_ids)}"
        )

    @staticmethod
    async def sync_module_role_deleted(
        session: AsyncSession,
        module_id: str,
        role_code: str,
    ) -> None:
        """
        同步模块角色删除事件

        删除所有已分配该模块的租户的角色。

        Args:
            session: 数据库会话
            module_id: 模块 ID
            role_code: 角色编码
        """
        from tenant.models import TenantModule

        # 1. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 2. 删除每个租户的角色
        deleted_count = 0
        for tenant_id in tenant_ids:
            # 查找租户角色
            role_stmt = select(Role).where(
                Role.tenant_id == tenant_id,
                Role.code == role_code,
            )
            role_result = await session.execute(role_stmt)
            tenant_role = role_result.scalar_one_or_none()

            if tenant_role:
                # 先删除用户角色关联
                from iam.models import UserRole

                await session.execute(
                    delete(UserRole).where(
                        UserRole.tenant_id == tenant_id,
                        UserRole.role_id == tenant_role.id,
                    )
                )

                # 删除角色权限关联
                await session.execute(
                    delete(RolePermission).where(
                        RolePermission.tenant_id == tenant_id,
                        RolePermission.role_id == tenant_role.id,
                    )
                )

                # 删除角色
                await session.delete(tenant_role)
                deleted_count += 1

        _logger.info(f"模块角色删除同步完成: role={role_code}, tenants={deleted_count}")

    @staticmethod
    async def sync_module_role_permission_created(
        session: AsyncSession,
        module_role_permission_id: str,
        module_id: str,
    ) -> None:
        """
        同步模块角色权限关联创建事件

        为所有已分配该模块的租户创建 RolePermission 记录。

        Args:
            session: 数据库会话
            module_role_permission_id: ModuleRolePermission ID
            module_id: 模块 ID
        """
        from tenant.models import ModuleRolePermission, TenantModule

        # 1. 获取模块角色权限关联信息
        mrp_stmt = select(ModuleRolePermission).where(
            ModuleRolePermission.id == module_role_permission_id
        )
        mrp_result = await session.execute(mrp_stmt)
        module_role_perm = mrp_result.scalar_one_or_none()
        if not module_role_perm:
            _logger.warning(f"模块角色权限关联不存在: {module_role_permission_id}")
            return

        # 2. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 3. 为每个租户创建角色权限关联
        created_count = 0
        for tenant_id in tenant_ids:
            # 查找租户角色（通过 ref_id）
            tenant_role_stmt = select(Role.id).where(
                Role.tenant_id == tenant_id,
                Role.ref_id == module_role_perm.module_role_id,
            )
            tenant_role_result = await session.execute(tenant_role_stmt)
            tenant_role_id = tenant_role_result.scalar_one_or_none()

            if not tenant_role_id:
                _logger.warning(
                    f"租户角色不存在: tenant_id={tenant_id}, "
                    f"module_role_id={module_role_perm.module_role_id}"
                )
                continue

            # 查找租户权限（通过 ref_id）
            tenant_perm_stmt = select(Permission.id).where(
                Permission.tenant_id == tenant_id,
                Permission.ref_id == module_role_perm.module_permission_id,
            )
            tenant_perm_result = await session.execute(tenant_perm_stmt)
            tenant_perm_id = tenant_perm_result.scalar_one_or_none()

            if not tenant_perm_id:
                _logger.warning(
                    f"租户权限不存在: tenant_id={tenant_id}, "
                    f"module_permission_id={module_role_perm.module_permission_id}"
                )
                continue

            # 幂等检查：查询是否已存在
            existing_rp_stmt = select(RolePermission).where(
                RolePermission.tenant_id == tenant_id,
                RolePermission.role_id == tenant_role_id,
                RolePermission.permission_id == tenant_perm_id,
            )
            existing_rp_result = await session.execute(existing_rp_stmt)
            if existing_rp_result.scalar_one_or_none():
                continue

            # 创建角色权限关联
            role_permission = RolePermission(
                tenant_id=tenant_id,
                role_id=tenant_role_id,
                permission_id=tenant_perm_id,
            )
            session.add(role_permission)
            created_count += 1

        # 触发权限缓存失效
        for tenant_id in tenant_ids:
            await PermissionCheckService.invalidate_tenant_permission_cache(
                session, tenant_id
            )

        _logger.info(
            f"模块角色权限关联创建同步完成: "
            f"module_role_permission_id={module_role_permission_id}, "
            f"tenants={len(tenant_ids)}, created={created_count}"
        )

    @staticmethod
    async def sync_module_role_permission_changed(
        session: AsyncSession,
        module_role_id: str,
        module_id: str,
    ) -> None:
        """
        同步模块角色权限变更事件

        更新所有已分配该模块的租户的角色权限。

        Args:
            session: 数据库会话
            module_role_id: 模块角色 ID
            module_id: 模块 ID
        """
        from tenant.models import (
            ModuleRolePermission,
            TenantModule,
        )

        # 1. 获取模块角色的权限列表
        mrp_stmt = select(ModuleRolePermission.module_permission_id).where(
            ModuleRolePermission.module_role_id == module_role_id
        )
        mrp_result = await session.execute(mrp_stmt)
        module_perm_ids = [row[0] for row in mrp_result.all()]

        # 2. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 3. 更新每个租户的角色权限
        for tenant_id in tenant_ids:
            # 查找租户角色
            tenant_role_stmt = select(Role.id).where(
                Role.tenant_id == tenant_id,
                Role.ref_id == module_role_id,
            )
            tenant_role_result = await session.execute(tenant_role_stmt)
            tenant_role_id = tenant_role_result.scalar_one_or_none()

            if not tenant_role_id:
                continue

            # 删除现有的角色权限关联
            await session.execute(
                delete(RolePermission).where(
                    RolePermission.tenant_id == tenant_id,
                    RolePermission.role_id == tenant_role_id,
                )
            )

            # 创建新的角色权限关联
            for module_perm_id in module_perm_ids:
                # 查找租户权限
                tenant_perm_stmt = select(Permission.id).where(
                    Permission.tenant_id == tenant_id,
                    Permission.ref_id == module_perm_id,
                )
                tenant_perm_result = await session.execute(tenant_perm_stmt)
                tenant_perm_id = tenant_perm_result.scalar_one_or_none()

                if tenant_perm_id:
                    role_permission = RolePermission(
                        tenant_id=tenant_id,
                        role_id=tenant_role_id,
                        permission_id=tenant_perm_id,
                    )
                    session.add(role_permission)

        # 触发权限缓存失效
        for tenant_id in tenant_ids:
            await PermissionCheckService.invalidate_tenant_permission_cache(
                session, tenant_id
            )

        _logger.info(
            f"模块角色权限变更同步完成: module_role_id={module_role_id}, tenants={len(tenant_ids)}"
        )

    @staticmethod
    async def sync_module_role_permission_deleted(
        session: AsyncSession,
        module_role_id: str,
        module_permission_id: str,
    ) -> None:
        """
        同步模块角色权限关联删除事件

        删除所有已分配该模块的租户对应的 RolePermission 记录。

        Args:
            session: 数据库会话
            module_role_id: 模块角色 ID
            module_permission_id: 模块权限 ID
        """
        # 1. 查找所有租户实例层中 ref_id=module_role_id 的 Role（含 tenant_id）
        role_stmt = select(Role.id, Role.tenant_id).where(Role.ref_id == module_role_id)
        role_result = await session.execute(role_stmt)
        role_rows = role_result.all()

        if not role_rows:
            _logger.warning(f"租户角色不存在: module_role_id={module_role_id}")
            return

        # 2. 逐租户删除对应的 RolePermission 记录
        deleted_count = 0
        for role_id, role_tenant_id in role_rows:
            # 查找该租户下 ref_id=module_permission_id 的 Permission
            # 通过 tenant_id 关联，确保删除的是同一租户的记录
            perm_stmt = select(Permission.id).where(
                Permission.tenant_id == role_tenant_id,
                Permission.ref_id == module_permission_id,
            )
            perm_result = await session.execute(perm_stmt)
            tenant_perm_id = perm_result.scalar_one_or_none()

            if not tenant_perm_id:
                _logger.warning(
                    f"租户权限不存在: tenant_id={role_tenant_id}, "
                    f"module_permission_id={module_permission_id}"
                )
                continue

            # 删除 RolePermission 记录
            deleted_stmt = delete(RolePermission).where(
                RolePermission.tenant_id == role_tenant_id,
                RolePermission.role_id == role_id,
                RolePermission.permission_id == tenant_perm_id,
            )
            deleted_result = await session.execute(deleted_stmt)
            deleted_count += deleted_result.rowcount

        # 触发权限缓存失效
        affected_tenant_ids = {role_tenant_id for _, role_tenant_id in role_rows}
        for tenant_id in affected_tenant_ids:
            await PermissionCheckService.invalidate_tenant_permission_cache(
                session, tenant_id
            )

        _logger.info(
            f"模块角色权限关联删除同步完成: "
            f"module_role_id={module_role_id}, "
            f"module_permission_id={module_permission_id}, "
            f"tenants={len(role_rows)}, deleted={deleted_count}"
        )

    @staticmethod
    async def sync_module_menu_permission_created(
        session: AsyncSession,
        module_menu_permission_id: str,
        module_id: str,
    ) -> None:
        """
        同步模块菜单权限关联创建事件

        为所有已分配该模块的租户创建 MenuPermission 记录。

        Args:
            session: 数据库会话
            module_menu_permission_id: ModuleMenuPermission ID
            module_id: 模块 ID
        """
        from tenant.models import ModuleMenuPermission, TenantModule

        # 1. 获取模块菜单权限关联信息
        mmp_stmt = select(ModuleMenuPermission).where(
            ModuleMenuPermission.id == module_menu_permission_id
        )
        mmp_result = await session.execute(mmp_stmt)
        module_menu_perm = mmp_result.scalar_one_or_none()
        if not module_menu_perm:
            _logger.warning(f"模块菜单权限关联不存在: {module_menu_permission_id}")
            return

        # 2. 查询所有已分配该模块的租户
        tm_stmt = select(TenantModule.tenant_id).where(
            TenantModule.module_id == module_id
        )
        tm_result = await session.execute(tm_stmt)
        tenant_ids = [row[0] for row in tm_result.all()]

        # 3. 为每个租户创建菜单权限关联
        created_count = 0
        for tenant_id in tenant_ids:
            # 查找租户菜单（通过 ref_id）
            tenant_menu_stmt = select(Menu.id).where(
                Menu.tenant_id == tenant_id,
                Menu.ref_id == module_menu_perm.module_menu_id,
            )
            tenant_menu_result = await session.execute(tenant_menu_stmt)
            tenant_menu_id = tenant_menu_result.scalar_one_or_none()

            if not tenant_menu_id:
                _logger.warning(
                    f"租户菜单不存在: tenant_id={tenant_id}, "
                    f"module_menu_id={module_menu_perm.module_menu_id}"
                )
                continue

            # 查找租户权限（通过 ref_id）
            tenant_perm_stmt = select(Permission.id).where(
                Permission.tenant_id == tenant_id,
                Permission.ref_id == module_menu_perm.module_permission_id,
            )
            tenant_perm_result = await session.execute(tenant_perm_stmt)
            tenant_perm_id = tenant_perm_result.scalar_one_or_none()

            if not tenant_perm_id:
                _logger.warning(
                    f"租户权限不存在: tenant_id={tenant_id}, "
                    f"module_permission_id={module_menu_perm.module_permission_id}"
                )
                continue

            # 幂等检查：通过 menu_id + permission_id 查询（MenuPermission 无 tenant_id）
            existing_mp_stmt = select(MenuPermission).where(
                MenuPermission.menu_id == tenant_menu_id,
                MenuPermission.permission_id == tenant_perm_id,
            )
            existing_mp_result = await session.execute(existing_mp_stmt)
            if existing_mp_result.scalar_one_or_none():
                continue

            # 创建菜单权限关联
            menu_permission = MenuPermission(
                menu_id=tenant_menu_id,
                permission_id=tenant_perm_id,
            )
            session.add(menu_permission)
            created_count += 1

        _logger.info(
            f"模块菜单权限关联创建同步完成: "
            f"module_menu_permission_id={module_menu_permission_id}, "
            f"tenants={len(tenant_ids)}, created={created_count}"
        )

    @staticmethod
    async def sync_module_menu_permission_deleted(
        session: AsyncSession,
        module_menu_id: str,
        module_permission_id: str,
    ) -> None:
        """
        同步模块菜单权限关联删除事件

        删除所有已分配该模块的租户对应的 MenuPermission 记录。

        Args:
            session: 数据库会话
            module_menu_id: 模块菜单 ID
            module_permission_id: 模块权限 ID
        """
        # 1. 查找所有租户实例层中 ref_id = module_menu_id 的 Menu（含 tenant_id）
        tenant_menus_stmt = select(Menu.id, Menu.tenant_id).where(
            Menu.ref_id == module_menu_id
        )
        tenant_menus_result = await session.execute(tenant_menus_stmt)
        tenant_menus_by_tenant: dict[str, list[str]] = defaultdict(list)
        for menu_id, tenant_id in tenant_menus_result.all():
            tenant_menus_by_tenant[tenant_id].append(menu_id)

        # 2. 查找所有租户实例层中 ref_id = module_permission_id 的 Permission（含 tenant_id）
        tenant_perms_stmt = select(Permission.id, Permission.tenant_id).where(
            Permission.ref_id == module_permission_id
        )
        tenant_perms_result = await session.execute(tenant_perms_stmt)
        tenant_perms_by_tenant: dict[str, list[str]] = defaultdict(list)
        for perm_id, tenant_id in tenant_perms_result.all():
            tenant_perms_by_tenant[tenant_id].append(perm_id)

        # 3. 按租户删除对应的 MenuPermission 记录
        deleted_count = 0
        for tenant_id, menu_ids in tenant_menus_by_tenant.items():
            perm_ids = tenant_perms_by_tenant.get(tenant_id, [])
            for menu_id in menu_ids:
                for perm_id in perm_ids:
                    delete_stmt = delete(MenuPermission).where(
                        MenuPermission.menu_id == menu_id,
                        MenuPermission.permission_id == perm_id,
                    )
                    result = await session.execute(delete_stmt)
                    deleted_count += result.rowcount

        _logger.info(
            f"模块菜单权限关联删除同步完成: "
            f"module_menu_id={module_menu_id}, "
            f"module_permission_id={module_permission_id}, "
            f"deleted={deleted_count}"
        )


# 服务单例
module_sync_service = ModuleSyncService()
