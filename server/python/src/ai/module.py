"""
AI 模块声明

定义 AI 模块的注册信息，包括路由、中间件、生命周期钩子和 Seed 数据。
"""

from collections.abc import Callable

from ai.models import Base
from framework.module.definition import (
    MenuDef,
    ModuleDefinition,
    PermissionDef,
)


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
        from ai.controllers.console.installations import router as installations_router
        from ai.controllers.console.plugin import router as console_plugin_router
        from ai.controllers.console.plugin_config_controller import (
            router as plugin_config_router,
        )
        from ai.controllers.console.runtime_states import (
            router as runtime_states_router,
        )
        from ai.controllers.inner.plugin import router as inner_plugin_router
        from ai.controllers.inner.plugin_management import (
            router as inner_plugin_management_router,
        )
        from ai.controllers.v1.chat.llm import router as chat_llm_router
        from ai.controllers.v1.conversation import router as conversation_router
        from ai.controllers.v1.model import router as model_router

        return [
            # Admin API - 插件管理
            (admin_plugin_router, "/ai/admin/v1/plugins", ["Admin - Plugin"]),
            # Console API - 插件安装管理（卸载、运行时管理、统计）
            # 注意：必须放在 console_plugin_router 之前，避免通配符路由拦截
            (
                installations_router,
                "/ai/console/v1/plugins/installations",
                ["Console - Plugin Installations"],
            ),
            # Console API - 插件配置管理（配置、测试、启动、停止）
            # 注意：路径参数版本，与 installations_router 共享前缀
            (
                plugin_config_router,
                "/ai/console/v1/plugins/installations",
                ["Console - Plugin Config"],
            ),
            # Console API - 批量运行时状态
            (
                runtime_states_router,
                "/ai/console/v1/plugins/runtime-states",
                ["Console - Runtime States"],
            ),
            # Console API - 插件列表和凭证管理
            (console_plugin_router, "/ai/console/v1/plugins", ["Console - Plugin"]),
            # Inner API - 内部接口
            (inner_plugin_router, "/ai/inner/v1", ["Inner - Plugin"]),
            # Inner API - 插件管理接口
            (inner_plugin_management_router, "/ai/inner/v1", ["Inner - Plugin Management"]),
            # Console API - LLM 对话接口
            (chat_llm_router, "/ai/console/v1", ["LLM对话"]),
            # Console API - 会话管理接口
            (conversation_router, "/ai/console/v1", ["会话管理"]),
            # Console API - 模型列表接口
            (model_router, "/ai/console/v1", ["模型列表"]),
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
        from ai.listeners.setup import cleanup_listeners, setup_listeners

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
                # 用户端菜单 - AI 对话
                MenuDef(
                    code="ai.chat",
                    name="AI 对话",
                    path="/ai",
                    icon="MessageSquare",
                    sort_order=1,
                    permission_codes=["ai:chat:read"],
                ),
                MenuDef(
                    code="ai.conversations",
                    name="会话列表",
                    path="/ai/conversations",
                    icon="List",
                    sort_order=2,
                    permission_codes=["ai:chat:read"],
                ),
                # 插件管理（合并安装和管理）
                MenuDef(
                    code="ai.plugins",
                    name="插件管理",
                    path="/ai/plugins",
                    icon="Puzzle",
                    sort_order=3,
                    permission_codes=["ai:plugin:read"],
                ),
                # plugins 隐藏二级菜单
                MenuDef(
                    code="ai.plugins.config",
                    name="插件配置",
                    path="/ai/plugins/{id}/config",
                    parent_code="ai.plugins",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["ai:plugin:write"],
                ),
                MenuDef(
                    code="ai.plugins.install",
                    name="安装插件",
                    path="/ai/plugins/install",
                    parent_code="ai.plugins",
                    sort_order=2,
                    is_visible=False,
                    permission_codes=["ai:plugin:write"],
                ),
            ],
            permissions=[
                # AI 对话权限（用户端）
                PermissionDef(
                    code="ai:chat:read",
                    name="使用 AI 对话",
                    resource="chat",
                    action="read",
                ),
                PermissionDef(
                    code="ai:chat:write",
                    name="发送对话消息",
                    resource="chat",
                    action="write",
                ),
                # 插件权限（管理端）
                PermissionDef(
                    code="ai:plugin:read",
                    name="查看插件",
                    resource="plugin",
                    action="read",
                ),
                PermissionDef(
                    code="ai:plugin:write",
                    name="编辑插件",
                    resource="plugin",
                    action="write",
                ),
                PermissionDef(
                    code="ai:plugin:delete",
                    name="删除插件",
                    resource="plugin",
                    action="delete",
                ),
            ],
        )
