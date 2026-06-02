from collections.abc import Mapping
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.sdk.entities.provider_config import CommonParameterType
from ai_plugin.sdk.entities.tool import (
    ParameterAutoGenerate,
    ParameterTemplate,
    ToolIdentity,
    ToolInvokeMessage,
    ToolParameterOption,
    ToolProviderIdentity,
)
from ai_plugin.server.core.documentation.schema_doc import docs
from ai_plugin.server.core.utils.yaml_loader import load_yaml_file


@docs(
    description="智能体策略提供者标识",
)
class AgentStrategyProviderIdentity(ToolProviderIdentity):
    """
    智能体策略提供者标识类

    继承自工具提供者标识，用于标识智能体策略提供者
    """

    pass


class AgentRuntime(BaseModel):
    """
    智能体运行时配置模型类

    存储智能体执行时的运行时信息
    """

    user_id: str | None  # 用户ID（可选）


@docs(
    description="智能体策略特性",
)
class AgentStrategyFeature(str, Enum):
    """
    智能体策略特性枚举类

    定义智能体策略支持的特性功能
    """

    HISTORY_MESSAGES = "history-messages"  # 历史消息特性


@docs(
    description="智能体策略标识",
)
class AgentStrategyIdentity(ToolIdentity):
    """
    智能体策略标识类

    继承自工具标识，用于标识具体的智能体策略
    """

    pass


@docs(
    description="智能体策略参数",
)
class AgentStrategyParameter(BaseModel):
    """
    智能体策略参数模型类

    定义智能体策略的参数配置信息
    """

    class ToolParameterType(str, Enum):
        """
        工具参数类型枚举

        定义智能体策略参数支持的各种数据类型
        """

        STRING = CommonParameterType.STRING.value  # 字符串类型
        NUMBER = CommonParameterType.NUMBER.value  # 数字类型
        BOOLEAN = CommonParameterType.BOOLEAN.value  # 布尔类型
        SELECT = CommonParameterType.SELECT.value  # 选择器类型
        SECRET_INPUT = CommonParameterType.SECRET_INPUT.value  # 密钥输入类型
        FILE = CommonParameterType.FILE.value  # 文件类型
        FILES = CommonParameterType.FILES.value  # 多文件类型
        MODEL_SELECTOR = CommonParameterType.MODEL_SELECTOR.value  # 模型选择器类型
        APP_SELECTOR = CommonParameterType.APP_SELECTOR.value  # 应用选择器类型
        TOOLS_SELECTOR = CommonParameterType.TOOLS_SELECTOR.value  # 工具组选择器类型
        # TOOL_SELECTOR = CommonParameterType.TOOL_SELECTOR.value  # 工具选择器类型（已废弃）
        ANY = CommonParameterType.ANY.value  # 任意类型

    name: str = Field(..., description="参数的名称")
    label: I18nObject = Field(..., description="呈现给用户的标签")
    help: I18nObject | None = None  # 帮助信息（可选）
    type: ToolParameterType = Field(..., description="参数的类型")
    auto_generate: ParameterAutoGenerate | None = Field(
        default=None, description="参数的自动生成配置"
    )
    template: ParameterTemplate | None = Field(
        default=None, description="参数的模板配置"
    )
    scope: str | None = None  # 作用域（可选）
    required: bool | None = False  # 是否必填
    default: int | float | str | None = None  # 默认值
    min: float | int | None = None  # 最小值
    max: float | int | None = None  # 最大值
    precision: int | None = None  # 精度
    options: list[ToolParameterOption] | None = None  # 选项列表


@docs(
    name="Python",
    description="智能体策略Python配置",
)
class Python(BaseModel):
    """
    Python配置模型类

    存储智能体策略的Python相关配置
    """

    source: str  # Python源码路径或内容


@docs(
    name="AgentStrategyExtra",
    description="智能体策略额外配置",
)
class AgentStrategyConfigurationExtra(BaseModel):
    """
    智能体策略配置额外信息模型类

    存储智能体策略的额外配置信息
    """

    python: Python  # Python配置


@docs(
    name="AgentStrategy",
    description="智能体策略配置清单",
)
class AgentStrategyConfiguration(BaseModel):
    """
    智能体策略配置模型类

    定义单个智能体策略的完整配置信息
    """

    identity: AgentStrategyIdentity  # 策略标识
    parameters: list[AgentStrategyParameter] = Field(
        default=[], description="智能体的参数列表"
    )
    description: I18nObject  # 策略描述
    extra: AgentStrategyConfigurationExtra  # 额外配置
    has_runtime_parameters: bool = Field(default=False, description="是否有运行时参数")
    output_schema: Mapping[str, Any] | None = None  # 输出架构（可选）
    features: list[AgentStrategyFeature] = Field(
        default=[], description="智能体的特性列表"
    )


@docs(
    name="AgentStrategyProviderExtra",
    description="智能体提供者额外配置",
)
class AgentProviderConfigurationExtra(BaseModel):
    """
    智能体提供者配置额外信息模型类

    存储智能体提供者的额外配置信息
    """

    @docs(
        name="Python",
        description="智能体提供者Python配置",
    )
    class Python(BaseModel):
        """
        Python配置子类

        存储智能体提供者的Python相关配置
        """

        source: str  # Python源码路径或内容

    python: Python  # Python配置


@docs(
    name="AgentStrategyProvider",
    description="智能体策略提供者配置清单",
    outside_reference_fields={"strategies": AgentStrategyConfiguration},
)
class AgentStrategyProviderConfiguration(BaseModel):
    """
    智能体策略提供者配置模型类

    定义智能体策略提供者的完整配置，包括标识和策略列表
    """

    identity: AgentStrategyProviderIdentity  # 提供者标识
    strategies: list[AgentStrategyConfiguration] = Field(
        default=[], description="智能体提供者的策略列表"
    )

    @field_validator("strategies", mode="before")
    @classmethod
    def validate_strategies(cls, value) -> list[AgentStrategyConfiguration]:
        """
        验证智能体策略配置列表

        从YAML文件加载智能体策略配置

        Args:
            value: 策略配置值

        Returns:
            list[AgentStrategyConfiguration]: 验证后的策略配置列表

        Raises:
            ValueError: 当配置格式无效时抛出
        """
        if not isinstance(value, list):
            raise ValueError("策略配置应该是一个列表")

        strategies: list[AgentStrategyConfiguration] = []

        for strategy in value:
            # 从YAML文件读取
            if isinstance(strategy, dict):
                # 兼容从数据库反序列化回来的数据
                strategies.append(AgentStrategyConfiguration(**strategy))
                continue

            if not isinstance(strategy, str):
                raise ValueError("策略路径应该是字符串")
            try:
                file = load_yaml_file(strategy)
                strategies.append(
                    AgentStrategyConfiguration(
                        **{
                            "identity": AgentStrategyIdentity(**file["identity"]),
                            "parameters": [
                                AgentStrategyParameter(**param)
                                for param in file.get("parameters", []) or []
                            ],
                            "description": I18nObject(**file["description"]),
                            "extra": AgentStrategyConfigurationExtra(
                                **file.get("extra", {})
                            ),
                            "features": file.get("features", []),
                        },
                    ),
                )
            except Exception as e:
                raise ValueError(f"加载智能体策略配置时出错: {e!s}") from e

        return strategies


class AgentInvokeMessage(ToolInvokeMessage):
    """
    智能体调用消息类

    继承自工具调用消息，用于智能体调用过程中的消息传递
    """

    pass
