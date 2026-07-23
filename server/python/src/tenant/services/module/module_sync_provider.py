"""
模块定义同步提供者实现

Tenant 模块对 ModuleDefinitionSyncProvider Protocol 的具体实现。
将模块定义（菜单、权限、角色）写入 tenant schema 的数据库表。
"""

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from framework.module.definition import (
    MenuDef,
    ModuleDefinition,
    PermissionDef,
    RoleDef,
)
from framework.tenant.sync_protocols import ModuleDefinitionSyncProvider
from tenant.models import (
    Module,
    ModuleMenu,
    ModuleMenuPermission,
    ModulePermission,
    ModuleRole,
    ModuleRolePermission,
)


class ModuleDefinitionSyncProviderImpl(ModuleDefinitionSyncProvider):
    """ModuleDefinitionSyncProvider 的 Tenant 模块实现"""

    async def upsert_module(
        self,
        session: AsyncSession,
        definition: ModuleDefinition,
    ) -> str:
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
        return result.scalar_one()

    async def get_menu_code_to_id_map(
        self,
        session: AsyncSession,
        module_id: str,
    ) -> dict[str, str]:
        stmt = select(ModuleMenu.id, ModuleMenu.code).where(
            ModuleMenu.module_id == module_id
        )
        result = await session.execute(stmt)
        return {row.code: row.id for row in result.all()}

    async def get_permission_code_to_id_map(
        self,
        session: AsyncSession,
        module_id: str,
    ) -> dict[str, str]:
        stmt = select(ModulePermission.id, ModulePermission.code).where(
            ModulePermission.module_id == module_id
        )
        result = await session.execute(stmt)
        return {row.code: row.id for row in result.all()}

    async def upsert_menu(
        self,
        session: AsyncSession,
        module_id: str,
        menu_def: MenuDef,
        parent_id: str | None,
        existing_menu_id: str | None,
    ) -> str:
        if existing_menu_id:
            # 更新已存在的菜单
            await ModuleMenu.update_node(
                session,
                existing_menu_id,
                {
                    "name": menu_def.name,
                    "path": menu_def.path,
                    "icon": menu_def.icon,
                    "tree_sort": menu_def.sort_order,
                    "is_visible": menu_def.is_visible,
                    "parent_id": parent_id,
                },
            )
            return existing_menu_id
        else:
            # 创建新菜单
            menu = await ModuleMenu.create_node(
                session,
                {
                    "module_id": module_id,
                    "parent_id": parent_id,
                    "code": menu_def.code,
                    "name": menu_def.name,
                    "path": menu_def.path,
                    "icon": menu_def.icon,
                    "tree_sort": menu_def.sort_order,
                    "is_visible": menu_def.is_visible,
                },
            )
            return menu.id

    async def upsert_permission(
        self,
        session: AsyncSession,
        module_id: str,
        perm_def: PermissionDef,
    ) -> None:
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

    async def delete_menu_permissions(
        self,
        session: AsyncSession,
        menu_id: str,
    ) -> None:
        stmt = delete(ModuleMenuPermission).where(
            ModuleMenuPermission.module_menu_id == menu_id
        )
        await session.execute(stmt)

    async def upsert_menu_permission(
        self,
        session: AsyncSession,
        menu_id: str,
        permission_id: str,
    ) -> None:
        stmt = (
            insert(ModuleMenuPermission)
            .values(
                module_menu_id=menu_id,
                module_permission_id=permission_id,
            )
            .on_conflict_do_nothing(
                constraint="uq_module_menu_permissions_menu_perm"
            )
        )
        await session.execute(stmt)

    async def upsert_role(
        self,
        session: AsyncSession,
        role_def: RoleDef,
        module_id: str | None,
    ) -> str:
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
        return result.scalar_one()

    async def delete_role_permissions(
        self,
        session: AsyncSession,
        role_id: str,
    ) -> None:
        stmt = delete(ModuleRolePermission).where(
            ModuleRolePermission.module_role_id == role_id
        )
        await session.execute(stmt)

    async def upsert_role_permission(
        self,
        session: AsyncSession,
        role_id: str,
        permission_id: str,
    ) -> None:
        stmt = (
            insert(ModuleRolePermission)
            .values(
                module_role_id=role_id,
                module_permission_id=permission_id,
            )
            .on_conflict_do_nothing(
                constraint="uq_module_role_permissions_role_perm"
            )
        )
        await session.execute(stmt)

    async def cleanup_orphans(
        self,
        session: AsyncSession,
        module_id: str,
        menus: list[MenuDef],
        permissions: list[PermissionDef],
        roles: list[RoleDef],
    ) -> None:
        # 清理孤儿菜单
        if menus:
            menu_codes = [m.code for m in menus]
            stmt = delete(ModuleMenu).where(
                ModuleMenu.module_id == module_id,
                ModuleMenu.code.not_in(menu_codes),
            )
            await session.execute(stmt)
        else:
            stmt = delete(ModuleMenu).where(ModuleMenu.module_id == module_id)
            await session.execute(stmt)

        # 清理孤儿权限
        if permissions:
            perm_codes = [p.code for p in permissions]
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
            role_codes = [r.code for r in roles]
            # 先获取要删除的角色 ID
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
                stmt = delete(ModuleRole).where(
                    ModuleRole.id.in_(role_ids_to_delete)
                )
                await session.execute(stmt)
        else:
            # 如果没有角色定义，删除该模块的所有角色
            stmt = select(ModuleRole.id).where(
                ModuleRole.module_id == module_id
            )
            result = await session.execute(stmt)
            role_ids = [row.id for row in result.all()]

            if role_ids:
                stmt = delete(ModuleRolePermission).where(
                    ModuleRolePermission.module_role_id.in_(role_ids)
                )
                await session.execute(stmt)
                stmt = delete(ModuleRole).where(
                    ModuleRole.module_id == module_id
                )
                await session.execute(stmt)

    async def get_all_permission_code_to_id_map(
        self,
        session: AsyncSession,
    ) -> dict[str, str]:
        stmt = select(ModulePermission.id, ModulePermission.code)
        result = await session.execute(stmt)
        return {row.code: row.id for row in result.all()}

    async def upsert_global_role(
        self,
        session: AsyncSession,
        role_def: RoleDef,
    ) -> str:
        # 全局角色 upsert 需要单独处理（module_id IS NULL 的特殊约束）
        stmt = select(ModuleRole).where(
            ModuleRole.module_id.is_(None),
            ModuleRole.code == role_def.code,
        )
        result = await session.execute(stmt)
        existing_role = result.scalar_one_or_none()

        if existing_role:
            existing_role.name = role_def.name
            existing_role.description = role_def.description
            existing_role.is_system = role_def.is_system
            await session.flush()
            return existing_role.id
        else:
            role = ModuleRole(
                module_id=None,
                code=role_def.code,
                name=role_def.name,
                description=role_def.description,
                is_system=role_def.is_system,
            )
            session.add(role)
            await session.flush()
            return role.id

    async def delete_orphan_global_roles(
        self,
        session: AsyncSession,
        valid_codes: list[str],
    ) -> None:
        # 查找要删除的全局角色 ID
        stmt = select(ModuleRole.id).where(
            ModuleRole.module_id.is_(None),
            ModuleRole.code.not_in(valid_codes),
        )
        result = await session.execute(stmt)
        orphan_role_ids = [row.id for row in result.all()]

        if orphan_role_ids:
            # 删除角色权限关联
            stmt = delete(ModuleRolePermission).where(
                ModuleRolePermission.module_role_id.in_(orphan_role_ids)
            )
            await session.execute(stmt)
            # 删除角色
            stmt = delete(ModuleRole).where(
                ModuleRole.id.in_(orphan_role_ids)
            )
            await session.execute(stmt)


# 单例实例
module_definition_sync_provider_impl = ModuleDefinitionSyncProviderImpl()
