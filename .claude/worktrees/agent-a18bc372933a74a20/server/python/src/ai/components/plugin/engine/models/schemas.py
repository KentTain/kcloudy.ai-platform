"""
插件配置模式定义
"""

from typing import Any

from pydantic import Field

from framework.schemas import BaseModel
from ai_plugin.sdk.entities.agent import AgentStrategyProviderConfiguration
from ai_plugin.sdk.entities.model.provider import ModelProviderConfiguration
from ai_plugin.sdk.entities.tool import ToolProviderConfiguration
from ai_plugin.server.core.entities.plugin.setup import PluginConfiguration


class PluginConfig(BaseModel):
    """
    插件配置类

    负责加载和管理插件的配置、工具、模型、代理策略等组件，
    """

    # 插件基础配置
    configuration: PluginConfiguration

    # 工具提供者配置列表
    tools_configuration: list[ToolProviderConfiguration] | None = Field(
        default=None, description="工具提供者配置列表"
    )

    # 代理策略提供者配置列表
    agent_strategies_configuration: list[AgentStrategyProviderConfiguration] | None = (
        Field(
            default=None,
            description="代理策略提供者配置列表",
        )
    )

    # 模型提供者配置列表
    models_configuration: list[ModelProviderConfiguration] | None = Field(
        default=None,
        description="模型提供者配置列表",
    )
