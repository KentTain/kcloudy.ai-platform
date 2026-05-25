"""
模块声明协议

定义模块必须实现的接口，用于动态加载和装配。
"""

from typing import Protocol, Any, Callable
from fastapi import FastAPI


class ModuleDescriptor(Protocol):
    """
    模块声明协议

    模块通过实现此协议来声明注册信息，包括：
    - 模块名称和 schema
    - 数据库 Base
    - 路由、中间件、生命周期钩子
    - Seed 数据、任务、监听器配置
    """

    @property
    def name(self) -> str:
        """
        模块名称

        用于标识模块，通常与目录名一致。
        例如: "iam", "demo"
        """
        ...

    @property
    def schema(self) -> str:
        """
        PostgreSQL schema 名称

        模块的数据库表将创建在此 schema 下。
        通常与模块名一致。
        """
        ...

    @property
    def dependencies(self) -> list[str]:
        """
        依赖的其他模块

        返回模块名列表，系统会确保依赖模块先加载。
        例如: ["iam"] 表示依赖 IAM 模块
        """
        ...

    def get_base(self) -> type:
        """
        返回模块的 DeclarativeBase

        用于数据库迁移和模型注册。
        """
        ...

    def get_routers(self) -> list[tuple]:
        """
        返回路由注册列表

        返回格式: [(router, prefix, tags), ...]
        - router: FastAPI APIRouter 实例
        - prefix: 路由前缀，如 "/api/v1"
        - tags: OpenAPI 标签列表，如 ["IAM"]
        """
        ...

    def get_middlewares(self) -> list[type]:
        """
        返回中间件列表

        返回中间件类列表，按顺序注册到应用。
        """
        ...

    def get_lifespan_hooks(self) -> list[Callable]:
        """
        返回生命周期钩子

        返回异步函数列表，在应用启动时执行。
        """
        ...

    def get_seeds(self) -> dict[str, Callable]:
        """
        返回 seed 注册表

        返回 {seed_name: seed_func} 字典。
        seed_func 签名: async def seed_func(dry_run: bool) -> None
        """
        ...

    def get_task_setup(self) -> tuple | None:
        """
        返回任务调度器配置

        返回 (setup_func, cleanup_func) 元组或 None。
        - setup_func: 注册定时任务的函数
        - cleanup_func: 清理定时任务的函数
        """
        ...

    def get_listener_setup(self) -> tuple | None:
        """
        返回监听器配置

        返回 (setup_func, cleanup_func) 元组或 None。
        - setup_func: 注册监听器的函数
        - cleanup_func: 清理监听器的函数
        """
        ...
