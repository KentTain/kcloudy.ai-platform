"""
IAM 模块声明

定义 IAM 模块的注册信息，包括路由、中间件、生命周期钩子和 Seed 数据。
"""

from typing import Callable

from framework.module.definition import (
    MenuDef,
    ModuleDefinition,
    PermissionDef,
    RoleDef,
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
        from iam.controllers import router as iam_router
        from iam.controllers.admin.system_setting_controller import router as admin_system_setting_router
        from iam.controllers.console.system_setting_controller import router as console_system_setting_router
        from iam.controllers.inner.user_controller import router as inner_user_router
        from iam.controllers.inner.department_controller import router as inner_department_router
        from iam.controllers.inner.tenant_menu_controller import router as inner_tenant_menu_router
        from iam.controllers.inner.tenant_permission_controller import router as inner_tenant_permission_router
        from iam.controllers.inner.tenant_role_controller import router as inner_tenant_role_router
        from iam.controllers.user_menu_controller import router as user_menu_router

        return [
            (iam_router, "/api/v1", ["IAM"]),
            (user_menu_router, "/api/v1/user", ["User Menu"]),
            (admin_system_setting_router, "/admin/v1/system-settings", ["Admin - SystemSetting"]),
            (console_system_setting_router, "/console/v1/system-settings", ["Console - SystemSetting"]),
            (inner_user_router, "/inner/v1", ["Inner - User"]),
            (inner_department_router, "/inner/v1", ["Inner - Department"]),
            (inner_tenant_menu_router, "/inner/v1/iam", ["Inner - Tenant Menu"]),
            (inner_tenant_permission_router, "/inner/v1/iam", ["Inner - Tenant Permission"]),
            (inner_tenant_role_router, "/inner/v1/iam", ["Inner - Tenant Role"]),
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
        """
        from iam.migrations.seeds.iam_seed import run as iam_seed_run
        from iam.migrations.seeds.user_seed import run as user_seed_run
        from iam.migrations.seeds.admin_seed import run as admin_seed_run
        # 暂时禁用 menu_seed 以测试登录功能
        # from iam.migrations.seeds.menu_seed import run as menu_seed_run

        return {
            "iam": iam_seed_run,
            "user": user_seed_run,
            "admin": admin_seed_run,
            # "menu": menu_seed_run,
        }

    def get_task_setup(self) -> tuple | None:
        """IAM 模块无定时任务"""
        return None

    def get_listener_setup(self) -> tuple | None:
        """
        返回监听器配置

        返回 (setup_func, cleanup_func) 元组
        """
        from iam.listeners.setup import setup_listeners, cleanup_listeners
        return (setup_listeners, cleanup_listeners)

    def get_module_definition(self) -> ModuleDefinition:
        """
        返回 IAM 模块的元数据定义

        包括菜单、权限、默认角色等声明
        """
        return ModuleDefinition(
            code="iam",
            name="身份与访问管理",
            description="用户认证、授权、角色权限管理",
            icon="Shield",
            version="1.0.0",
            menus=[
                MenuDef(code="iam.users", name="用户管理", path="/iam/users", icon="Users", sort_order=1),
                MenuDef(code="iam.roles", name="角色管理", path="/iam/roles", icon="Badge", sort_order=2),
                MenuDef(code="iam.departments", name="部门管理", path="/iam/departments", icon="Building", sort_order=3),
                MenuDef(code="iam.tenants", name="租户管理", path="/iam/tenants", icon="Organization", sort_order=4),
                MenuDef(code="iam.menus", name="菜单管理", path="/iam/menus", icon="Menu", sort_order=5),
                MenuDef(code="iam.permissions", name="权限管理", path="/iam/permissions", icon="Lock", sort_order=6),
            ],
            permissions=[
                # 用户权限
                PermissionDef(code="iam:user:read", name="查看用户", resource="user", action="read"),
                PermissionDef(code="iam:user:write", name="编辑用户", resource="user", action="write"),
                PermissionDef(code="iam:user:delete", name="删除用户", resource="user", action="delete"),
                # 角色权限
                PermissionDef(code="iam:role:read", name="查看角色", resource="role", action="read"),
                PermissionDef(code="iam:role:write", name="编辑角色", resource="role", action="write"),
                PermissionDef(code="iam:role:delete", name="删除角色", resource="role", action="delete"),
                # 部门权限
                PermissionDef(code="iam:department:read", name="查看部门", resource="department", action="read"),
                PermissionDef(code="iam:department:write", name="编辑部门", resource="department", action="write"),
                PermissionDef(code="iam:department:delete", name="删除部门", resource="department", action="delete"),
                # 租户权限
                PermissionDef(code="iam:tenant:read", name="查看租户", resource="tenant", action="read"),
                PermissionDef(code="iam:tenant:write", name="编辑租户", resource="tenant", action="write"),
                PermissionDef(code="iam:tenant:delete", name="删除租户", resource="tenant", action="delete"),
                # 菜单权限
                PermissionDef(code="iam:menu:read", name="查看菜单", resource="menu", action="read"),
                PermissionDef(code="iam:menu:write", name="编辑菜单", resource="menu", action="write"),
                PermissionDef(code="iam:menu:delete", name="删除菜单", resource="menu", action="delete"),
                # 权限管理权限
                PermissionDef(code="iam:permission:read", name="查看权限", resource="permission", action="read"),
                PermissionDef(code="iam:permission:write", name="编辑权限", resource="permission", action="write"),
                PermissionDef(code="iam:permission:delete", name="删除权限", resource="permission", action="delete"),
            ],
            default_roles=[
                RoleDef(
                    code="admin",
                    name="管理员",
                    description="IAM 模块管理员，拥有所有权限",
                    permission_codes=["iam:*:*"],
                    is_system=True,
                ),
                RoleDef(
                    code="viewer",
                    name="查看者",
                    description="IAM 模块只读用户",
                    permission_codes=["iam:*:read"],
                    is_system=True,
                ),
            ],
        )
