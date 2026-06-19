from decimal import Decimal
from enum import Enum, StrEnum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.server.core.documentation.schema_doc import docs


@docs(
    description="默认参数名称",
)
class DefaultParameterName(Enum):
    """
    参数模板变量枚举类

    定义模型参数的默认名称常量
    """

    TEMPERATURE = "temperature"  # 温度参数
    TOP_P = "top_p"  # Top P采样参数
    TOP_K = "top_k"  # Top K采样参数
    PRESENCE_PENALTY = "presence_penalty"  # 存在惩罚参数
    FREQUENCY_PENALTY = "frequency_penalty"  # 频率惩罚参数
    MAX_TOKENS = "max_tokens"  # 最大令牌数参数
    RESPONSE_FORMAT = "response_format"  # 响应格式参数
    JSON_SCHEMA = "json_schema"  # JSON架构参数

    @classmethod
    def value_of(cls, value: Any) -> "DefaultParameterName":
        """
        根据值获取参数名称

        Args:
            value: 参数值

        Returns:
            DefaultParameterName: 对应的参数名称枚举

        Raises:
            ValueError: 当参数名称无效时抛出
        """
        for name in cls:
            if name.value == value:
                return name
        raise ValueError(f"无效的参数名称 {value}")


# 参数规则模板字典，包含各种参数的默认配置
PARAMETER_RULE_TEMPLATE: dict[DefaultParameterName, dict] = {
    DefaultParameterName.TEMPERATURE: {
        "label": {
            "en_US": "Temperature",
            "zh_Hans": "温度",
        },
        "type": "float",
        "help": {
            "en_US": "Controls randomness. Lower temperature results in less random completions. As the temperature approaches zero, the model will become deterministic and repetitive. Higher temperature results in more random completions.",
            "zh_Hans": "温度控制随机性。较低的温度会导致较少的随机完成。随着温度接近零，模型将变得确定性和重复性。"
            "较高的温度会导致更多的随机完成。",
        },
        "required": False,
        "default": 0.0,
        "min": 0.0,
        "max": 1.0,
        "precision": 2,
    },
    DefaultParameterName.TOP_P: {
        "label": {
            "en_US": "Top P",
            "zh_Hans": "Top P",
        },
        "type": "float",
        "help": {
            "en_US": "Controls diversity via nucleus sampling: "
            "0.5 means half of all likelihood-weighted options are considered.",
            "zh_Hans": "通过核心采样控制多样性：0.5表示考虑了一半的所有可能性加权选项。",
        },
        "required": False,
        "default": 1.0,
        "min": 0.0,
        "max": 1.0,
        "precision": 2,
    },
    DefaultParameterName.TOP_K: {
        "label": {
            "en_US": "Top K",
            "zh_Hans": "Top K",
        },
        "type": "int",
        "help": {
            "en_US": "Limits the number of tokens to consider for each step by keeping only the k most likely tokens.",
            "zh_Hans": "通过只保留每一步中最可能的 k 个标记来限制要考虑的标记数量。",
        },
        "required": False,
        "default": 50,
        "min": 1,
        "max": 100,
        "precision": 0,
    },
    DefaultParameterName.PRESENCE_PENALTY: {
        "label": {
            "en_US": "Presence Penalty",
            "zh_Hans": "存在惩罚",
        },
        "type": "float",
        "help": {
            "en_US": "Applies a penalty to the log-probability of tokens already in the text.",
            "zh_Hans": "对文本中已有的标记的对数概率施加惩罚。",
        },
        "required": False,
        "default": 0.0,
        "min": 0.0,
        "max": 1.0,
        "precision": 2,
    },
    DefaultParameterName.FREQUENCY_PENALTY: {
        "label": {
            "en_US": "Frequency Penalty",
            "zh_Hans": "频率惩罚",
        },
        "type": "float",
        "help": {
            "en_US": "Applies a penalty to the log-probability of tokens that appear in the text.",
            "zh_Hans": "对文本中出现的标记的对数概率施加惩罚。",
        },
        "required": False,
        "default": 0.0,
        "min": 0.0,
        "max": 1.0,
        "precision": 2,
    },
    DefaultParameterName.MAX_TOKENS: {
        "label": {
            "en_US": "Max Tokens",
            "zh_Hans": "最大标记",
        },
        "type": "int",
        "help": {
            "en_US": "Specifies the upper limit on the length of generated results. "
            "If the generated results are truncated, you can increase this parameter.",
            "zh_Hans": "指定生成结果长度的上限。如果生成结果截断，可以调大该参数。",
        },
        "required": False,
        "default": 64,
        "min": 1,
        "max": 2048,
        "precision": 0,
    },
    DefaultParameterName.RESPONSE_FORMAT: {
        "label": {
            "en_US": "Response Format",
            "zh_Hans": "回复格式",
        },
        "type": "string",
        "help": {
            "en_US": "Set a response format, ensure the output from llm is a valid code block as possible, "
            "such as JSON, XML, etc.",
            "zh_Hans": "设置一个返回格式，确保llm的输出尽可能是有效的代码块，如JSON、XML等",
        },
        "required": False,
        "options": ["JSON", "XML"],
    },
    DefaultParameterName.JSON_SCHEMA: {
        "label": {
            "en_US": "JSON Schema",
        },
        "type": "text",
        "help": {
            "en_US": "Set a response json schema will ensure LLM to adhere it.",
            "zh_Hans": "设置返回的json schema，llm将按照它返回",
        },
        "required": False,
    },
}


@docs(
    description="模型类型",
)
class ModelType(StrEnum):
    """
    模型类型枚举类

    定义支持的各种AI模型类型
    """

    LLM = "llm"  # 大语言模型
    TEXT_EMBEDDING = "text-embedding"  # 文本嵌入模型
    RERANK = "rerank"  # 重排序模型
    SPEECH2TEXT = "speech2text"  # 语音转文本模型
    MODERATION = "moderation"  # 内容审核模型
    TTS = "tts"  # 文本转语音模型
    TEXT2IMG = "text2img"  # 文本转图像模型


@docs(
    description="获取来源",
)
class FetchFrom(Enum):
    """
    获取来源枚举类

    定义模型的获取来源方式
    """

    PREDEFINED_MODEL = "predefined-model"  # 预定义模型
    CUSTOMIZABLE_MODEL = "customizable-model"  # 可自定义模型


@docs(
    description="模型特性",
)
class ModelFeature(Enum):
    """
    LLM特性枚举类

    定义大语言模型支持的各种特性功能
    """

    TOOL_CALL = "tool-call"  # 工具调用
    MULTI_TOOL_CALL = "multi-tool-call"  # 多工具调用
    AGENT_THOUGHT = "agent-thought"  # 智能体思考
    VISION = "vision"  # 视觉能力
    STREAM_TOOL_CALL = "stream-tool-call"  # 流式工具调用
    DOCUMENT = "document"  # 文档处理
    VIDEO = "video"  # 视频处理
    AUDIO = "audio"  # 音频处理
    STRUCTURED_OUTPUT = "structured-output"  # 结构化输出


@docs(
    description="参数类型",
)
class ParameterType(Enum):
    """
    参数类型枚举类

    定义模型参数支持的数据类型
    """

    FLOAT = "float"  # 浮点数
    INT = "int"  # 整数
    STRING = "string"  # 字符串
    BOOLEAN = "boolean"  # 布尔值
    TEXT = "text"  # 文本


@docs(
    description="模型属性键",
)
class ModelPropertyKey(Enum):
    """
    模型属性键枚举类

    定义模型的各种属性键名
    """

    MODE = "mode"  # 模式
    CONTEXT_SIZE = "context_size"  # 上下文大小
    MAX_CHUNKS = "max_chunks"  # 最大块数
    FILE_UPLOAD_LIMIT = "file_upload_limit"  # 文件上传限制
    SUPPORTED_FILE_EXTENSIONS = "supported_file_extensions"  # 支持的文件扩展名
    MAX_CHARACTERS_PER_CHUNK = "max_characters_per_chunk"  # 每块最大字符数
    DEFAULT_VOICE = "default_voice"  # 默认语音
    VOICES = "voices"  # 语音列表
    WORD_LIMIT = "word_limit"  # 字数限制
    AUDIO_TYPE = "audio_type"  # 音频类型
    MAX_WORKERS = "max_workers"  # 最大工作者数


@docs(
    description="提供者模型",
)
class ProviderModel(BaseModel):
    """
    提供者模型类

    定义模型提供者的基本模型信息
    """

    model: str = Field(..., description="模型名称")
    label: I18nObject = Field(..., description="模型的标签")
    model_type: ModelType = Field(..., description="模型类型")
    features: list[ModelFeature] | None = Field(
        default=None, description="模型的特性列表"
    )
    fetch_from: FetchFrom = Field(
        default=FetchFrom.PREDEFINED_MODEL, description="获取来源"
    )
    model_properties: dict[ModelPropertyKey, Any] = Field(..., description="模型属性")
    deprecated: bool = Field(default=False, description="是否已废弃")
    model_config = ConfigDict(protected_namespaces=())

    @model_validator(mode="before")
    @classmethod
    def validate_label(cls, data: dict) -> dict:
        """
        验证标签，使用模型名作为标签

        Args:
            data: 模型数据字典

        Returns:
            dict: 验证后的数据
        """
        if isinstance(data, dict) and not data.get("label"):
            data["label"] = I18nObject(en_US=data["model"])

        return data


@docs(
    description="模型的参数规则",
)
class ParameterRule(BaseModel):
    """
    参数规则模型类

    定义模型参数的验证和显示规则
    """

    name: str = Field(..., description="参数的名称")
    use_template: str | None = Field(default=None, description="参数的模板")
    label: I18nObject = Field(..., description="参数的标签")
    type: ParameterType = Field(..., description="参数的类型")
    help: I18nObject | None = Field(default=None, description="参数的帮助信息")
    required: bool = Field(default=False, description="参数是否必填")
    default: Any | None = Field(default=None, description="参数的默认值")
    min: float | None = Field(default=None, description="参数的最小值")
    max: float | None = Field(default=None, description="参数的最大值")
    precision: int | None = Field(default=None, description="参数的精度")
    options: list[str] = Field(default=[], description="参数的选项列表")

    @model_validator(mode="before")
    @classmethod
    def validate_label(cls, data: dict) -> dict:
        """
        验证标签，支持使用模板参数

        Args:
            data: 参数数据字典

        Returns:
            dict: 验证后的数据

        Raises:
            Exception: 当参数规则模板无效时抛出
        """
        if isinstance(data, dict):
            # 检查是否有模板
            if "use_template" in data:
                try:
                    default_parameter_name = DefaultParameterName.value_of(
                        data["use_template"]
                    )
                    default_parameter_rule = PARAMETER_RULE_TEMPLATE.get(
                        default_parameter_name
                    )
                    if not default_parameter_rule:
                        raise Exception(
                            f"无效的模型参数规则名称 {default_parameter_name}"
                        )
                    copy_default_parameter_rule = default_parameter_rule.copy()
                    copy_default_parameter_rule.update(data)
                    data = copy_default_parameter_rule
                except ValueError:
                    pass

            if not data.get("label"):
                data["label"] = I18nObject(en_US=data["name"])

        return data


@docs(
    description="价格配置",
)
class PriceConfig(BaseModel):
    """
    定价信息模型类

    定义模型的价格配置信息
    """

    input: Decimal = Field(..., description="输入价格")
    output: Decimal | None = Field(default=None, description="输出价格")
    unit: Decimal = Field(..., description="单位，例如 0.0001 -> 每10000个令牌")
    currency: str = Field(..., description="货币，例如 USD")


@docs(
    description="AI模型实体",
)
class AIModelEntity(ProviderModel):
    """
    AI模型实体类

    继承自提供者模型，包含参数规则和价格信息
    """

    parameter_rules: list[ParameterRule] = []  # 参数规则列表
    pricing: PriceConfig | None = None  # 价格配置（可选）


class ModelUsage(BaseModel):
    """
    模型使用情况基类

    用于记录模型的使用统计信息
    """

    pass


class PriceType(Enum):
    """
    价格类型枚举类

    定义价格的不同类型
    """

    INPUT = "input"  # 输入价格
    OUTPUT = "output"  # 输出价格


class PriceInfo(BaseModel):
    """
    价格信息模型类

    定义详细的价格计算信息
    """

    unit_price: Decimal = Field(..., description="单价，例如 0.000001")
    unit: Decimal = Field(..., description="单位，例如 1000")
    total_amount: Decimal = Field(..., description="总金额")
    currency: str = Field(..., description="货币，例如 USD")


class BaseModelConfig(BaseModel):
    """
    基础模型配置类

    定义模型的基本配置信息
    """

    provider: str  # 提供者
    model: str  # 模型名称
    model_type: ModelType  # 模型类型

    model_config = ConfigDict(protected_namespaces=())


class EmbeddingInputType(Enum):
    """
    嵌入输入类型枚举

    定义文本嵌入的输入类型
    """

    DOCUMENT = "document"  # 文档类型
    QUERY = "query"  # 查询类型
