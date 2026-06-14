"""
AI 模块声明

定义 AI 模块的注册信息，包括路由、中间件、生命周期钩子和 Seed 数据。
"""

from typing import Callable

from framework.module.definition import (
    MenuDef,
    ModuleDefinition,
    PermissionDef,
    RoleDef,
)

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
        # AI 依赖 IAM 模块（跨 schema 外键引用 iam.users）
        return ["tenant", "iam"]

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
        from ai.controllers.v1.chat.llm import router as chat_llm_router
        from ai.controllers.v1.conversation import router as conversation_router
        from ai.controllers.v1.model import router as model_router

        return [
            # Admin API - 插件管理
            (admin_plugin_router, "/admin/v1/plugins", ["Admin - Plugin"]),
            # Console API - 插件列表和凭证管理
            (console_plugin_router, "/console/v1/plugins", ["Console - Plugin"]),
            # Inner API - 内部接口
            (inner_plugin_router, "/inner/v1", ["Inner - Plugin"]),
            # V1 API - LLM 对话接口
            (chat_llm_router, "/api/v1", ["LLM对话"]),
            # V1 API - 会话管理接口
            (conversation_router, "/api/v1", ["会话管理"]),
            # V1 API - 模型列表接口
            (model_router, "/api/v1", ["模型列表"]),
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

    def get_module_definition(self) -> ModuleDefinition:
        """
        返回 AI 模块的元数据定义

        包括菜单、权限、默认角色等声明
        """
        return ModuleDefinition(
            code="ai",
            name="AI 能力",
            description="AI 插件管理、模型调用、智能助手",
            icon="Robot",
            version="1.0.0",
            menus=[
                MenuDef(code="ai.plugins", name="插件管理", path="/ai/plugins", icon="Puzzle", sort_order=1),
            ],
            permissions=[
                # 插件权限
                PermissionDef(code="ai:plugin:read", name="查看插件", resource="plugin", action="read"),
                PermissionDef(code="ai:plugin:write", name="编辑插件", resource="plugin", action="write"),
                PermissionDef(code="ai:plugin:delete", name="删除插件", resource="plugin", action="delete"),
            ],
            default_roles=[
                RoleDef(
                    code="admin",
                    name="管理员",
                    description="AI 模块管理员，拥有所有权限",
                    permission_codes=["ai:*:*"],
                    is_system=True,
                ),
                RoleDef(
                    code="viewer",
                    name="查看者",
                    description="AI 模块只读用户",
                    permission_codes=["ai:*:read"],
                    is_system=True,
                ),
            ],
        )
