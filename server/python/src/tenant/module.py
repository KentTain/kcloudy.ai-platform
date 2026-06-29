"""
Tenant 模块声明

定义 Tenant 模块的注册信息，包括路由、中间件、生命周期钩子和 Seed 数据。
"""

from collections.abc import Callable

from framework.module.definition import (
    MenuDef,
    ModuleDefinition,
    PermissionDef,
    RoleDef,
)
from tenant.models import Base


class TenantModule:
    """Tenant 模块描述符"""

    @property
    def name(self) -> str:
        return "tenant"

    @property
    def schema(self) -> str:
        return "tenant"

    @property
    def dependencies(self) -> list[str]:
        # Tenant 是基础模块，无依赖
        return []

    def get_base(self) -> type:
        return Base

    def get_routers(self) -> list[tuple]:
        """
        返回路由注册列表

        格式: [(router, prefix, tags), ...]
        """
        from tenant.controllers.admin.module_controller import (
            router as admin_module_router,
        )
        from tenant.controllers.admin.plugin_controller import (
            router as admin_plugin_router,
        )
        from tenant.controllers.admin.resource_controller import (
            router as admin_resource_router,
        )
        from tenant.controllers.admin.tenant_controller import (
            router as admin_tenant_router,
        )
        from tenant.controllers.admin.tenant_module_controller import (
            router as admin_tenant_module_router,
        )
        from tenant.controllers.console.tenant_controller import (
            router as console_tenant_router,
        )
        from tenant.controllers.inner.tenant_controller import (
            router as inner_tenant_router,
        )

        return [
            (admin_tenant_router, "/tenant/admin/v1", ["Admin - Tenant"]),
            (admin_resource_router, "/tenant/admin/v1", ["Admin - Resource Config"]),
            (admin_module_router, "/tenant/admin/v1", ["Admin - Module"]),
            (admin_plugin_router, "/tenant/admin/v1", ["Admin - Plugin"]),
            (admin_tenant_module_router, "/tenant/admin/v1", ["Admin - Tenant Module"]),
            (console_tenant_router, "/tenant/console/v1/tenants", ["Console - Tenant"]),
            (inner_tenant_router, "/tenant/inner/v1", ["Inner - Tenant"]),
        ]

    def get_middlewares(self) -> list[type]:
        """返回中间件列表"""
        from tenant.middlewares.admin_auth_middleware import AdminAuthMiddleware

        return [AdminAuthMiddleware]

    def get_lifespan_hooks(self) -> list[Callable]:
        """返回生命周期钩子"""
        return []

    def get_seeds(self) -> dict[str, Callable]:
        """
        返回 seed 注册表

        格式: {seed_name: seed_func}

        注意：Python 3.7+ 字典保持插入顺序，seed 按依赖顺序注册：
          1. resource_config  # 资源配置（无依赖）
          2. global_role      # 全局角色（无依赖）
          3. tenant           # 默认租户（依赖 resource_config）
          4. admin            # 默认管理员（依赖 tenant）
        """
        from tenant.migrations.seeds.admin_seed import run as admin_seed_run
        from tenant.migrations.seeds.global_role_seed import (
            run as global_role_seed_run,
        )
        from tenant.migrations.seeds.resource_config_seed import (
            run as resource_config_seed_run,
        )
        from tenant.migrations.seeds.tenant_seed import run as tenant_seed_run

        return {
            "resource_config": resource_config_seed_run,
            "global_role": global_role_seed_run,
            "tenant": tenant_seed_run,
            "admin": admin_seed_run,
        }

    def get_task_setup(self) -> tuple | None:
        """Tenant 模块定时任务"""
        from tenant.tasks.setup import cleanup_scheduler, setup_scheduler

        return (setup_scheduler, cleanup_scheduler)

    def get_listener_setup(self) -> tuple | None:
        """Tenant 模块消息监听器

        处理插件安装/卸载失败事件，保障跨 Schema 数据一致性。
        """
        from tenant.listeners.setup import cleanup_listeners, setup_listeners
        return (setup_listeners, cleanup_listeners)

    def get_module_definition(self) -> ModuleDefinition:
        """
        返回 Tenant 模块的元数据定义

        包括菜单、权限、默认角色等声明
        """
        return ModuleDefinition(
            code="tenant",
            name="租户管理",
            description="多租户系统管理、模块管理、资源配置",
            icon="Organization",
            version="1.0.0",
            menus=[
                MenuDef(
                    code="tenant.modules",
                    name="模块管理",
                    path="/admin/modules",
                    icon="Puzzle",
                    sort_order=1,
                    permission_codes=["tenant:module:read"],
                ),
                # modules 隐藏二级菜单
                MenuDef(
                    code="tenant.modules.create",
                    name="创建模块",
                    path="/admin/modules/create",
                    parent_code="tenant.modules",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["tenant:module:write"],
                ),
                MenuDef(
                    code="tenant.modules.detail",
                    name="模块详情",
                    path="/admin/modules/{id}",
                    parent_code="tenant.modules",
                    sort_order=2,
                    is_visible=False,
                    permission_codes=["tenant:module:read"],
                ),
                MenuDef(
                    code="tenant.modules.edit",
                    name="编辑模块",
                    path="/admin/modules/{id}/edit",
                    parent_code="tenant.modules",
                    sort_order=3,
                    is_visible=False,
                    permission_codes=["tenant:module:write"],
                ),
                MenuDef(
                    code="tenant.tenants",
                    name="租户管理",
                    path="/admin/tenants",
                    icon="Organization",
                    sort_order=2,
                    permission_codes=["tenant:tenant:read"],
                ),
                # tenants 隐藏二级菜单
                MenuDef(
                    code="tenant.tenants.create",
                    name="创建租户",
                    path="/admin/tenants/create",
                    parent_code="tenant.tenants",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["tenant:tenant:write"],
                ),
                MenuDef(
                    code="tenant.tenants.detail",
                    name="租户详情",
                    path="/admin/tenants/{id}",
                    parent_code="tenant.tenants",
                    sort_order=2,
                    is_visible=False,
                    permission_codes=["tenant:tenant:read"],
                ),
                MenuDef(
                    code="tenant.tenants.edit",
                    name="编辑租户",
                    path="/admin/tenants/{id}/edit",
                    parent_code="tenant.tenants",
                    sort_order=3,
                    is_visible=False,
                    permission_codes=["tenant:tenant:write"],
                ),
                MenuDef(
                    code="tenant.resources",
                    name="资源配置",
                    path="/admin/resources",
                    icon="Settings",
                    sort_order=3,
                    permission_codes=["tenant:resource:read"],
                ),
                # resources 隐藏二级菜单
                MenuDef(
                    code="tenant.resources.create",
                    name="创建资源配置",
                    path="/admin/resources/create",
                    parent_code="tenant.resources",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["tenant:resource:write"],
                ),
                MenuDef(
                    code="tenant.resources.detail",
                    name="资源配置详情",
                    path="/admin/resources/{id}",
                    parent_code="tenant.resources",
                    sort_order=2,
                    is_visible=False,
                    permission_codes=["tenant:resource:read"],
                ),
                MenuDef(
                    code="tenant.resources.edit",
                    name="编辑资源配置",
                    path="/admin/resources/{id}/edit",
                    parent_code="tenant.resources",
                    sort_order=3,
                    is_visible=False,
                    permission_codes=["tenant:resource:write"],
                ),
                # plugin-definitions 插件定义
                MenuDef(
                    code="tenant.plugin-definitions",
                    name="插件定义",
                    path="/admin/plugin-definitions",
                    icon="Puzzle",
                    sort_order=4,
                    permission_codes=["tenant:plugin:read"],
                ),
                # plugin-definitions 隐藏二级菜单
                MenuDef(
                    code="tenant.plugin-definitions.create",
                    name="新增插件定义",
                    path="/admin/plugin-definitions/create",
                    parent_code="tenant.plugin-definitions",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["tenant:plugin:write"],
                ),
                MenuDef(
                    code="tenant.plugin-definitions.detail",
                    name="查看插件定义详情",
                    path="/admin/plugin-definitions/{id}",
                    parent_code="tenant.plugin-definitions",
                    sort_order=2,
                    is_visible=False,
                    permission_codes=["tenant:plugin:read"],
                ),
                MenuDef(
                    code="tenant.plugin-definitions.edit",
                    name="编辑插件定义",
                    path="/admin/plugin-definitions/{id}/edit",
                    parent_code="tenant.plugin-definitions",
                    sort_order=3,
                    is_visible=False,
                    permission_codes=["tenant:plugin:write"],
                ),
            ],
            default_roles=[
                RoleDef(
                    code="tenantAdmin",
                    name="租户管理员",
                    description="拥有租户管理模块的所有读写权限",
                    permission_codes=["tenant:*:*"],
                    is_system=True,
                ),
                RoleDef(
                    code="ordinaryAdmin",
                    name="普通管理员",
                    description="拥有租户管理模块的只读权限",
                    permission_codes=["tenant:*:read"],
                    is_system=True,
                ),
            ],
            permissions=[
                # 模块权限
                PermissionDef(
                    code="tenant:module:read",
                    name="查看模块",
                    resource="module",
                    action="read",
                ),
                PermissionDef(
                    code="tenant:module:write",
                    name="编辑模块",
                    resource="module",
                    action="write",
                ),
                PermissionDef(
                    code="tenant:module:delete",
                    name="删除模块",
                    resource="module",
                    action="delete",
                ),
                # 租户权限
                PermissionDef(
                    code="tenant:tenant:read",
                    name="查看租户",
                    resource="tenant",
                    action="read",
                ),
                PermissionDef(
                    code="tenant:tenant:write",
                    name="编辑租户",
                    resource="tenant",
                    action="write",
                ),
                PermissionDef(
                    code="tenant:tenant:delete",
                    name="删除租户",
                    resource="tenant",
                    action="delete",
                ),
                # 资源配置权限
                PermissionDef(
                    code="tenant:resource:read",
                    name="查看资源配置",
                    resource="resource",
                    action="read",
                ),
                PermissionDef(
                    code="tenant:resource:write",
                    name="编辑资源配置",
                    resource="resource",
                    action="write",
                ),
                PermissionDef(
                    code="tenant:resource:delete",
                    name="删除资源配置",
                    resource="resource",
                    action="delete",
                ),
                # 插件定义管理
                PermissionDef(
                    code="tenant:plugin:read",
                    name="查看插件定义",
                    resource="plugin",
                    action="read",
                ),
                PermissionDef(
                    code="tenant:plugin:write",
                    name="编辑插件定义",
                    resource="plugin",
                    action="write",
                ),
                PermissionDef(
                    code="tenant:plugin:delete",
                    name="删除插件定义",
                    resource="plugin",
                    action="delete",
                ),
            ],
        )
