from enum import Enum

from pydantic import BaseModel, Field

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.server.core.documentation.schema_doc import docs


class LogMetadata(str, Enum):
    """
    日志元数据枚举类

    定义了日志记录中使用的各种元数据字段
    """

    STARTED_AT = "started_at"  # 开始时间
    FINISHED_AT = "finished_at"  # 结束时间
    ELAPSED_TIME = "elapsed_time"  # 耗时
    TOTAL_PRICE = "total_price"  # 总价格
    TOTAL_TOKENS = "total_tokens"  # 总令牌数
    PROVIDER = "provider"  # 提供者
    CURRENCY = "currency"  # 货币


@docs(
    description="参数类型",
)
class CommonParameterType(Enum):
    """
    通用参数类型枚举类

    定义了插件配置中支持的各种参数类型
    """

    SECRET_INPUT = "secret-input"  # 密钥输入
    TEXT_INPUT = "text-input"  # 文本输入
    SELECT = "select"  # 选择器
    STRING = "string"  # 字符串
    NUMBER = "number"  # 数字
    FILE = "file"  # 单个文件
    FILES = "files"  # 多个文件
    BOOLEAN = "boolean"  # 布尔值
    APP_SELECTOR = "app-selector"  # 应用选择器
    MODEL_SELECTOR = "model-selector"  # 模型选择器
    # TOOL_SELECTOR = "tool-selector"    # 工具选择器（已废弃）
    TOOLS_SELECTOR = "array[tools]"  # 工具组选择器
    ANY = "any"  # 任意类型


@docs(
    description="应用选择器范围",
)
class AppSelectorScope(Enum):
    """
    应用选择器范围枚举类

    定义了应用选择器可以选择的应用类型范围
    """

    ALL = "all"  # 所有类型
    CHAT = "chat"  # 聊天应用
    WORKFLOW = "workflow"  # 工作流应用
    COMPLETION = "completion"  # 文本补全应用


@docs(
    description="模型配置范围",
)
class ModelConfigScope(Enum):
    """
    模型配置范围枚举类

    定义了模型配置支持的各种模型类型
    """

    LLM = "llm"  # 大语言模型
    TEXT_EMBEDDING = "text-embedding"  # 文本嵌入模型
    RERANK = "rerank"  # 重排序模型
    TTS = "tts"  # 文本转语音模型
    SPEECH2TEXT = "speech2text"  # 语音转文本模型
    MODERATION = "moderation"  # 内容审核模型
    VISION = "vision"  # 视觉模型


@docs(
    description="工具选择器范围",
)
class ToolSelectorScope(Enum):
    """
    工具选择器范围枚举类

    定义了工具选择器可以选择的工具类型范围
    """

    ALL = "all"  # 所有工具
    PLUGIN = "plugin"  # 插件工具
    API = "api"  # API工具
    WORKFLOW = "workflow"  # 工作流工具


@docs(
    description="凭证配置选项",
)
class ConfigOption(BaseModel):
    """
    配置选项模型类

    用于定义选择器类型参数的可选项
    """

    value: str = Field(..., description="选项的值")
    label: I18nObject = Field(..., description="选项的标签")


@docs(
    description="通用配置架构",
)
class ProviderConfig(BaseModel):
    """
    提供者配置模型类

    定义了插件提供者的配置参数架构，包括参数名称、类型、是否必填等信息
    """

    class Config(Enum):
        """
        配置类型枚举子类

        定义了配置参数支持的各种类型
        """

        SECRET_INPUT = CommonParameterType.SECRET_INPUT.value  # 密钥输入
        TEXT_INPUT = CommonParameterType.TEXT_INPUT.value  # 文本输入
        SELECT = CommonParameterType.SELECT.value  # 选择器
        BOOLEAN = CommonParameterType.BOOLEAN.value  # 布尔值
        MODEL_SELECTOR = CommonParameterType.MODEL_SELECTOR.value  # 模型选择器
        APP_SELECTOR = CommonParameterType.APP_SELECTOR.value  # 应用选择器
        # TOOL_SELECTOR = CommonParameterType.TOOL_SELECTOR.value # 工具选择器（已废弃）
        TOOLS_SELECTOR = CommonParameterType.TOOLS_SELECTOR.value  # 工具组选择器

        @classmethod
        def value_of(cls, value: str) -> "ProviderConfig.Config":
            """
            根据给定值获取对应的配置类型

            Args:
                value: 配置类型值

            Returns:
                ProviderConfig.Config: 配置类型枚举

            Raises:
                ValueError: 当配置类型值无效时抛出
            """
            for mode in cls:
                if mode.value == value:
                    return mode
            raise ValueError(f"无效的配置类型值 {value}")

    name: str = Field(..., description="凭证的名称")
    type: Config = Field(..., description="凭证的类型")
    scope: str | None = None  # 作用域（可选）
    required: bool = False  # 是否必填
    default: int | float | str | None = None  # 默认值
    options: list[ConfigOption] | None = None  # 选项列表（用于选择器类型）
    label: I18nObject  # 参数标签
    help: I18nObject | None = None  # 帮助文本
    url: str | None = None  # 相关URL
    placeholder: I18nObject | None = None  # 占位符文本
