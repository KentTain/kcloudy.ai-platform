"""
模块定义同步提供者协议

定义 ModuleDefinitionSyncProvider Protocol，抽象 tenant schema 的数据库操作。
通过依赖倒置避免 framework 直接依赖 tenant 业务模块。
"""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from framework.module.definition import (
    MenuDef,
    ModuleDefinition,
    PermissionDef,
    RoleDef,
)


class ModuleDefinitionSyncProvider(Protocol):
    """
    模块定义同步提供者协议

    将模块定义（菜单、权限、角色）持久化到数据库的抽象接口。
    - 本地部署：由 Tenant 模块基于 SQLAlchemy ORM 实现
    - 分布式部署：可由其他模块基于 HTTP/gRPC 实现
    """

    async def upsert_module(
        self,
        session: AsyncSession,
        definition: ModuleDefinition,
    ) -> str:
        """
        创建或更新 Module 记录

        Args:
            session: 数据库会话
            definition: 模块定义

        Returns:
            模块 ID
        """
        ...

    async def get_menu_code_to_id_map(
        self,
        session: AsyncSession,
        module_id: str,
    ) -> dict[str, str]:
        """
        获取模块菜单的 code -> id 映射

        Args:
            session: 数据库会话
            module_id: 模块 ID

        Returns:
            {code: id}
        """
        ...

    async def get_permission_code_to_id_map(
        self,
        session: AsyncSession,
        module_id: str,
    ) -> dict[str, str]:
        """
        获取模块权限的 code -> id 映射

        Args:
            session: 数据库会话
            module_id: 模块 ID

        Returns:
            {code: id}
        """
        ...

    async def upsert_menu(
        self,
        session: AsyncSession,
        module_id: str,
        menu_def: MenuDef,
        parent_id: str | None,
        existing_menu_id: str | None,
    ) -> str:
        """
        创建或更新菜单

        Args:
            session: 数据库会话
            module_id: 模块 ID
            menu_def: 菜单定义
            parent_id: 父菜单 ID（None 表示根菜单）
            existing_menu_id: 已存在菜单的 ID（None 表示新建）

        Returns:
            菜单 ID
        """
        ...

    async def upsert_permission(
        self,
        session: AsyncSession,
        module_id: str,
        perm_def: PermissionDef,
    ) -> None:
        """
        创建或更新权限

        Args:
            session: 数据库会话
            module_id: 模块 ID
            perm_def: 权限定义
        """
        ...

    async def delete_menu_permissions(
        self,
        session: AsyncSession,
        menu_id: str,
    ) -> None:
        """
        删除菜单的所有权限关联

        Args:
            session: 数据库会话
            menu_id: 菜单 ID
        """
        ...

    async def upsert_menu_permission(
        self,
        session: AsyncSession,
        menu_id: str,
        permission_id: str,
    ) -> None:
        """
        创建菜单-权限关联

        Args:
            session: 数据库会话
            menu_id: 菜单 ID
            permission_id: 权限 ID
        """
        ...

    async def upsert_role(
        self,
        session: AsyncSession,
        role_def: RoleDef,
        module_id: str | None,
    ) -> str:
        """
        创建或更新角色

        当 module_id 为 None 时视为全局角色。

        Args:
            session: 数据库会话
            role_def: 角色定义
            module_id: 所属模块 ID（None 表示全局角色）

        Returns:
            角色 ID
        """
        ...

    async def delete_role_permissions(
        self,
        session: AsyncSession,
        role_id: str,
    ) -> None:
        """
        删除角色的所有权限关联

        Args:
            session: 数据库会话
            role_id: 角色 ID
        """
        ...

    async def upsert_role_permission(
        self,
        session: AsyncSession,
        role_id: str,
        permission_id: str,
    ) -> None:
        """
        创建角色-权限关联

        Args:
            session: 数据库会话
            role_id: 角色 ID
            permission_id: 权限 ID
        """
        ...

    async def cleanup_orphans(
        self,
        session: AsyncSession,
        module_id: str,
        menus: list[MenuDef],
        permissions: list[PermissionDef],
        roles: list[RoleDef],
    ) -> None:
        """
        清理孤儿数据

        删除数据库中已不存在于模块定义的菜单、权限、角色。

        Args:
            session: 数据库会话
            module_id: 模块 ID
            menus: 当前菜单定义列表
            permissions: 当前权限定义列表
            roles: 当前角色定义列表
        """
        ...

    async def get_all_permission_code_to_id_map(
        self,
        session: AsyncSession,
    ) -> dict[str, str]:
        """
        获取所有模块的权限 code -> id 映射（用于全局角色同步）

        Args:
            session: 数据库会话

        Returns:
            {code: id}
        """
        ...

    async def upsert_global_role(
        self,
        session: AsyncSession,
        role_def: RoleDef,
    ) -> str:
        """
        创建或更新全局角色（module_id IS NULL）

        Args:
            session: 数据库会话
            role_def: 角色定义

        Returns:
            角色 ID
        """
        ...

    async def delete_orphan_global_roles(
        self,
        session: AsyncSession,
        valid_codes: list[str],
    ) -> None:
        """
        删除不再存在的全局角色

        Args:
            session: 数据库会话
            valid_codes: 有效的全局角色 code 列表
        """
        ...


# =============================================================================
# 全局注册
# =============================================================================

_sync_provider: ModuleDefinitionSyncProvider | None = None


def register_module_definition_sync_provider(
    provider: ModuleDefinitionSyncProvider,
) -> None:
    """
    注册模块定义同步提供者

    应用启动时调用，由 Tenant 模块注入具体实现。

    Args:
        provider: ModuleDefinitionSyncProvider 实现实例
    """
    global _sync_provider
    _sync_provider = provider


def get_module_definition_sync_provider() -> ModuleDefinitionSyncProvider:
    """
    获取模块定义同步提供者

    Returns:
        ModuleDefinitionSyncProvider 实例

    Raises:
        RuntimeError: 未注册时抛出
    """
    if _sync_provider is None:
        raise RuntimeError(
            "ModuleDefinitionSyncProvider not registered. "
            "Call register_module_definition_sync_provider() at startup."
        )
    return _sync_provider
