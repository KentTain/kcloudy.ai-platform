"""
Tenant 模块声明

定义 Tenant 模块的注册信息，包括路由、中间件、生命周期钩子和 Seed 数据。
"""

from typing import Callable

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
        from tenant.controllers.admin.tenant_controller import router as admin_tenant_router
        from tenant.controllers.console.tenant_controller import router as console_tenant_router
        from tenant.controllers.inner.tenant_controller import router as inner_tenant_router

        return [
            (admin_tenant_router, "/admin/v1", ["Admin - Tenant"]),
            (console_tenant_router, "/console/v1/tenants", ["Console - Tenant"]),
            (inner_tenant_router, "/inner/v1", ["Inner - Tenant"]),
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
        """
        from tenant.migrations.seeds.tenant_seed import run as tenant_seed_run

        return {
            "tenant": tenant_seed_run,
        }

    def get_task_setup(self) -> tuple | None:
        """Tenant 模块无定时任务"""
        return None

    def get_listener_setup(self) -> tuple | None:
        """Tenant 模块无消息监听器"""
        return None
