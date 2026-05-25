"""
IAM 模块声明

定义 IAM 模块的注册信息，包括路由、中间件、生命周期钩子和 Seed 数据。
"""

from typing import Callable

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
        # IAM 是基础模块，无依赖
        return []

    def get_base(self) -> type:
        return Base

    def get_routers(self) -> list[tuple]:
        """
        返回路由注册列表

        格式: [(router, prefix, tags), ...]
        """
        from iam.controllers import router as iam_router
        from iam.controllers.admin.tenant_controller import router as admin_tenant_router
        from iam.controllers.admin.system_setting_controller import router as admin_system_setting_router
        from iam.controllers.console.tenant_controller import router as console_tenant_router
        from iam.controllers.console.system_setting_controller import router as console_system_setting_router

        return [
            (iam_router, "/api/v1", ["IAM"]),
            (admin_tenant_router, "/admin/v1", ["Admin - Tenant"]),
            (admin_system_setting_router, "/admin/v1/system-settings", ["Admin - SystemSetting"]),
            (console_tenant_router, "/console/v1/tenants", ["Console - Tenant"]),
            (console_system_setting_router, "/console/v1/system-settings", ["Console - SystemSetting"]),
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
        from iam.migrations.seeds.tenant_seed import run as tenant_seed_run
        from iam.migrations.seeds.iam_seed import run as iam_seed_run
        from iam.migrations.seeds.admin_seed import run as admin_seed_run

        return {
            "tenant": tenant_seed_run,
            "iam": iam_seed_run,
            "admin": admin_seed_run,
        }

    def get_task_setup(self) -> tuple | None:
        """IAM 模块无定时任务"""
        return None

    def get_listener_setup(self) -> tuple | None:
        """IAM 模块无消息监听器"""
        return None
