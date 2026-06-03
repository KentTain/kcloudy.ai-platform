"""
AI 模块声明

定义 AI 模块的注册信息，包括路由、中间件、生命周期钩子和 Seed 数据。
"""

from typing import Callable

from ai.models import Base


class AIModule:
    """AI 模块描述符"""

    @property
    def name(self) -> str:
        return "ai"

    @property
    def schema(self) -> str:
        return "ai"

    @property
    def dependencies(self) -> list[str]:
        # AI 依赖 Tenant 模块（通过 inner 接口获取租户信息）
        return ["tenant"]

    def get_base(self) -> type:
        return Base

    def get_routers(self) -> list[tuple]:
        """
        返回路由注册列表

        格式: [(router, prefix, tags), ...]
        """
        from ai.controllers.admin.plugin import router as admin_plugin_router
        from ai.controllers.console.plugin import router as console_plugin_router
        from ai.controllers.inner.plugin import router as inner_plugin_router

        return [
            # Admin API - 插件管理
            (admin_plugin_router, "/admin/v1/plugins", ["Admin - Plugin"]),
            # Console API - 插件列表和凭证管理
            (console_plugin_router, "/console/v1/plugins", ["Console - Plugin"]),
            # Inner API - 内部接口
            (inner_plugin_router, "/inner/v1", ["Inner - Plugin"]),
        ]

    def get_middlewares(self) -> list[type]:
        """
        返回中间件列表

        AI 模块使用全局租户中间件，无需额外中间件
        """
        return []

    def get_lifespan_hooks(self) -> list[Callable]:
        """
        返回生命周期钩子

        AI 模块的初始化逻辑（如插件引擎初始化）在应用层处理
        """
        return []

    def get_seeds(self) -> dict[str, Callable]:
        """
        返回 seed 注册表

        AI 模块暂无种子数据
        """
        return {}

    def get_task_setup(self) -> tuple | None:
        """AI 模块无定时任务"""
        return None

    def get_listener_setup(self) -> tuple | None:
        """返回监听器配置"""
        from ai.listeners.setup import setup_listeners, cleanup_listeners
        return (setup_listeners, cleanup_listeners)
