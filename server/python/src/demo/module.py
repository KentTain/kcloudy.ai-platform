from collections.abc import Callable

from demo.models import Base
from framework.module.definition import ModuleDefinition


class DemoModule:
    """Demo 模块描述符"""

    @property
    def name(self) -> str:
        return "demo"

    @property
    def schema(self) -> str:
        return "demo"

    @property
    def dependencies(self) -> list[str]:
        # Demo 依赖 IAM 模块的租户数据
        return ["iam"]

    def get_base(self) -> type:
        return Base

    def get_routers(self) -> list[tuple]:
        """
        返回路由注册列表

        格式: [(router, prefix, tags), ...]
        """
        from demo.controllers.dataset import router as dataset_router

        return [
            (dataset_router, "/api/v1/datasets", ["Dataset"]),
        ]

    def get_middlewares(self) -> list[type]:
        """
        返回中间件列表

        注意：TenantMiddleware 在 framework 层注册，不属于单个模块
        """
        return []

    def get_lifespan_hooks(self) -> list[Callable]:
        """返回生命周期钩子"""
        return []

    def get_seeds(self) -> dict[str, Callable]:
        """
        返回 seed 注册表

        Demo 模块暂无独立 seed
        """
        return {}

    def get_task_setup(self) -> tuple | None:
        """
        返回任务调度器配置

        返回 (setup_func, cleanup_func) 元组
        """
        from demo.tasks.setup import cleanup_scheduler, setup_scheduler

        return (setup_scheduler, cleanup_scheduler)

    def get_listener_setup(self) -> tuple | None:
        """
        返回监听器配置

        返回 (setup_func, cleanup_func) 元组
        """
        from demo.listeners.setup import cleanup_listeners, setup_listeners

        return (setup_listeners, cleanup_listeners)

    def get_module_definition(self) -> ModuleDefinition | None:
        """
        返回模块定义（可选）

        Demo 模块暂无菜单/权限/角色声明。
        """
        return None
