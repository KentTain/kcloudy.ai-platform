"""
IAM 模块声明

定义 IAM 模块的注册信息，包括路由、中间件、生命周期钩子和 Seed 数据。
"""

from collections.abc import Callable

from framework.module.definition import (
    MenuDef,
    ModuleDefinition,
    PermissionDef,
)
from iam.models import Base


class IAMModule:
    """IAM 模块描述符"""

    @property
    def name(self) -> str:
        return "iam"

    @property
    def schema(self) -> str:
        return "iam"

    @property
    def dependencies(self) -> list[str]:
        # IAM 依赖 Tenant 模块
        return ["tenant"]

    def get_base(self) -> type:
        return Base

    def get_routers(self) -> list[tuple]:
        """
        返回路由注册列表

        格式: [(router, prefix, tags), ...]
        """
        # Admin 层
        from iam.controllers.admin.menu_controller import router as admin_menu_router
        from iam.controllers.admin.organization_controller import (
            router as admin_organization_router,
        )
        from iam.controllers.admin.permission_controller import (
            router as admin_permission_router,
        )
        from iam.controllers.admin.role_controller import router as admin_role_router
        from iam.controllers.admin.system_setting_controller import (
            router as admin_system_setting_router,
        )
        from iam.controllers.admin.user_controller import router as admin_user_router

        # Console 层
        from iam.controllers.console.auth_controller import (
            router as console_auth_router,
        )
        from iam.controllers.console.oauth_controller import (
            router as console_oauth_router,
        )
        from iam.controllers.console.org_user_controller import (
            router as console_org_user_router,
        )
        from iam.controllers.console.system_setting_controller import (
            router as console_system_setting_router,
        )
        from iam.controllers.console.user_controller import (
            router as console_user_router,
        )
        from iam.controllers.inner.organization_controller import (
            router as inner_organization_router,
        )
        from iam.controllers.inner.tenant_menu_controller import (
            router as inner_tenant_menu_router,
        )
        from iam.controllers.inner.tenant_permission_controller import (
            router as inner_tenant_permission_router,
        )
        from iam.controllers.inner.tenant_role_controller import (
            router as inner_tenant_role_router,
        )

        # Inner 层
        from iam.controllers.inner.user_controller import router as inner_user_router

        return [
            # Admin 层路由
            (admin_user_router, "/iam/admin/v1", ["Admin - User"]),
            (admin_role_router, "/iam/admin/v1", ["Admin - Role"]),
            (admin_permission_router, "/iam/admin/v1", ["Admin - Permission"]),
            (admin_organization_router, "/iam/admin/v1", ["Admin - Organization"]),
            (admin_menu_router, "/iam/admin/v1", ["Admin - Menu"]),
            (
                admin_system_setting_router,
                "/iam/admin/v1/system-settings",
                ["Admin - SystemSetting"],
            ),
            # Console 层路由
            (console_auth_router, "/iam/console/v1", ["Console - Auth"]),
            (console_oauth_router, "/iam/console/v1", ["Console - OAuth"]),
            (console_org_user_router, "/iam/console/v1", ["Console - OrgUser"]),
            (console_user_router, "/iam/console/v1", ["Console - User"]),
            (
                console_system_setting_router,
                "/iam/console/v1/system-settings",
                ["Console - SystemSetting"],
            ),
            # Inner 层路由
            (inner_user_router, "/iam/inner/v1", ["Inner - User"]),
            (inner_organization_router, "/iam/inner/v1", ["Inner - Organization"]),
            (inner_tenant_menu_router, "/iam/inner/v1", ["Inner - Tenant Menu"]),
            (
                inner_tenant_permission_router,
                "/iam/inner/v1",
                ["Inner - Tenant Permission"],
            ),
            (inner_tenant_role_router, "/iam/inner/v1", ["Inner - Tenant Role"]),
        ]

    def get_middlewares(self) -> list[type]:
        """
        返回中间件列表

        注意：TenantMiddleware 在 framework 层注册，不属于单个模块
        """
        return []

    def get_lifespan_hooks(self) -> list[Callable]:
        """
        返回生命周期钩子

        IAM 模块的初始化逻辑（如注册 TenantProvider）在应用层处理
        """
        return []

    def get_seeds(self) -> dict[str, Callable]:
        """
        返回 seed 注册表

        格式: {seed_name: seed_func}

        注意：Python 3.7+ 字典保持插入顺序，seed 按依赖顺序注册：
          5. organization  # 默认组织（依赖 tenant）
          6. user          # 默认用户（依赖 tenant, role, organization）
        """
        from iam.migrations.seeds.organization_seed import (
            run as organization_seed_run,
        )
        from iam.migrations.seeds.user_seed import run as user_seed_run

        return {
            "organization": organization_seed_run,
            "user": user_seed_run,
        }

    def get_task_setup(self) -> tuple | None:
        """IAM 模块无定时任务"""
        return None

    def get_listener_setup(self) -> tuple | None:
        """
        返回监听器配置

        返回 (setup_func, cleanup_func) 元组
        """
        from iam.listeners.setup import cleanup_listeners, setup_listeners

        return (setup_listeners, cleanup_listeners)

    def get_module_definition(self) -> ModuleDefinition:
        """
        返回 IAM 模块的元数据定义

        包括菜单、权限、默认角色等声明
        """
        return ModuleDefinition(
            code="iam",
            name="系统管理",
            description="用户认证、授权、角色权限管理",
            icon="Shield",
            version="1.0.0",
            menus=[
                MenuDef(
                    code="iam.organizations",
                    name="组织管理",
                    path="/iam/organizations",
                    icon="Building",
                    sort_order=1,
                    permission_codes=["iam:organization:read"],
                ),
                # organizations 隐藏二级菜单
                MenuDef(
                    code="iam.organizations.create",
                    name="创建组织",
                    path="/iam/organizations/create",
                    parent_code="iam.organizations",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["iam:organization:write"],
                ),
                MenuDef(
                    code="iam.organizations.detail",
                    name="组织详情",
                    path="/iam/organizations/{id}",
                    parent_code="iam.organizations",
                    sort_order=2,
                    is_visible=False,
                    permission_codes=["iam:organization:read"],
                ),
                MenuDef(
                    code="iam.organizations.edit",
                    name="编辑组织",
                    path="/iam/organizations/{id}/edit",
                    parent_code="iam.organizations",
                    sort_order=3,
                    is_visible=False,
                    permission_codes=["iam:organization:write"],
                ),
                MenuDef(
                    code="iam.roles",
                    name="角色管理",
                    path="/iam/roles",
                    icon="Badge",
                    sort_order=2,
                    permission_codes=["iam:role:read"],
                ),
                # roles 隐藏二级菜单
                MenuDef(
                    code="iam.roles.create",
                    name="创建角色",
                    path="/iam/roles/create",
                    parent_code="iam.roles",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["iam:role:write"],
                ),
                MenuDef(
                    code="iam.roles.detail",
                    name="角色详情",
                    path="/iam/roles/{id}",
                    parent_code="iam.roles",
                    sort_order=2,
                    is_visible=False,
                    permission_codes=["iam:role:read"],
                ),
                MenuDef(
                    code="iam.roles.edit",
                    name="编辑角色",
                    path="/iam/roles/{id}/edit",
                    parent_code="iam.roles",
                    sort_order=3,
                    is_visible=False,
                    permission_codes=["iam:role:write"],
                ),
                MenuDef(
                    code="iam.users",
                    name="用户管理",
                    path="/iam/users",
                    icon="Users",
                    sort_order=3,
                    permission_codes=["iam:user:read"],
                ),
                # users 隐藏二级菜单
                MenuDef(
                    code="iam.users.create",
                    name="创建用户",
                    path="/iam/users/create",
                    parent_code="iam.users",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["iam:user:write"],
                ),
                MenuDef(
                    code="iam.users.detail",
                    name="用户详情",
                    path="/iam/users/{id}",
                    parent_code="iam.users",
                    sort_order=2,
                    is_visible=False,
                    permission_codes=["iam:user:read"],
                ),
                MenuDef(
                    code="iam.users.edit",
                    name="编辑用户",
                    path="/iam/users/{id}/edit",
                    parent_code="iam.users",
                    sort_order=3,
                    is_visible=False,
                    permission_codes=["iam:user:write"],
                ),
                MenuDef(
                    code="iam.menus",
                    name="菜单管理",
                    path="/iam/menus",
                    icon="Menu",
                    sort_order=4,
                    permission_codes=["iam:menu:read"],
                ),
                # menus 隐藏二级菜单
                MenuDef(
                    code="iam.menus.create",
                    name="创建菜单",
                    path="/iam/menus/create",
                    parent_code="iam.menus",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["iam:menu:write"],
                ),
                MenuDef(
                    code="iam.menus.detail",
                    name="菜单详情",
                    path="/iam/menus/{id}",
                    parent_code="iam.menus",
                    sort_order=2,
                    is_visible=False,
                    permission_codes=["iam:menu:read"],
                ),
                MenuDef(
                    code="iam.menus.edit",
                    name="编辑菜单",
                    path="/iam/menus/{id}/edit",
                    parent_code="iam.menus",
                    sort_order=3,
                    is_visible=False,
                    permission_codes=["iam:menu:write"],
                ),
                MenuDef(
                    code="iam.permissions",
                    name="权限管理",
                    path="/iam/permissions",
                    icon="Lock",
                    sort_order=5,
                    permission_codes=["iam:permission:read"],
                ),
                # permissions 隐藏二级菜单
                MenuDef(
                    code="iam.permissions.create",
                    name="创建权限",
                    path="/iam/permissions/create",
                    parent_code="iam.permissions",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["iam:permission:write"],
                ),
                MenuDef(
                    code="iam.permissions.detail",
                    name="权限详情",
                    path="/iam/permissions/{id}",
                    parent_code="iam.permissions",
                    sort_order=2,
                    is_visible=False,
                    permission_codes=["iam:permission:read"],
                ),
                MenuDef(
                    code="iam.permissions.edit",
                    name="编辑权限",
                    path="/iam/permissions/{id}/edit",
                    parent_code="iam.permissions",
                    sort_order=3,
                    is_visible=False,
                    permission_codes=["iam:permission:write"],
                ),
            ],
            permissions=[
                # 用户权限
                PermissionDef(
                    code="iam:user:read",
                    name="查看用户",
                    resource="user",
                    action="read",
                ),
                PermissionDef(
                    code="iam:user:write",
                    name="编辑用户",
                    resource="user",
                    action="write",
                ),
                PermissionDef(
                    code="iam:user:delete",
                    name="删除用户",
                    resource="user",
                    action="delete",
                ),
                # 角色权限
                PermissionDef(
                    code="iam:role:read",
                    name="查看角色",
                    resource="role",
                    action="read",
                ),
                PermissionDef(
                    code="iam:role:write",
                    name="编辑角色",
                    resource="role",
                    action="write",
                ),
                PermissionDef(
                    code="iam:role:delete",
                    name="删除角色",
                    resource="role",
                    action="delete",
                ),
                # 组织权限
                PermissionDef(
                    code="iam:organization:read",
                    name="查看组织",
                    resource="organization",
                    action="read",
                ),
                PermissionDef(
                    code="iam:organization:write",
                    name="编辑组织",
                    resource="organization",
                    action="write",
                ),
                PermissionDef(
                    code="iam:organization:delete",
                    name="删除组织",
                    resource="organization",
                    action="delete",
                ),
                # 菜单权限
                PermissionDef(
                    code="iam:menu:read",
                    name="查看菜单",
                    resource="menu",
                    action="read",
                ),
                PermissionDef(
                    code="iam:menu:write",
                    name="编辑菜单",
                    resource="menu",
                    action="write",
                ),
                PermissionDef(
                    code="iam:menu:delete",
                    name="删除菜单",
                    resource="menu",
                    action="delete",
                ),
                # 权限管理权限
                PermissionDef(
                    code="iam:permission:read",
                    name="查看权限",
                    resource="permission",
                    action="read",
                ),
                PermissionDef(
                    code="iam:permission:write",
                    name="编辑权限",
                    resource="permission",
                    action="write",
                ),
                PermissionDef(
                    code="iam:permission:delete",
                    name="删除权限",
                    resource="permission",
                    action="delete",
                ),
            ],
        )
