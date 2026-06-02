from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai_plugin.sdk.entities.model import (
    BaseModelConfig,
    ModelType,
    ModelUsage,
    PriceInfo,
)
from ai_plugin.sdk.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
)


class LLMMode(Enum):
    """
    大语言模型模式枚举类

    定义大语言模型的运行模式
    """

    COMPLETION = "completion"  # 补全模式
    CHAT = "chat"  # 对话模式

    @classmethod
    def value_of(cls, value: str) -> "LLMMode":
        """
        根据值获取指定的模式

        Args:
            value: 模式值

        Returns:
            LLMMode: 对应的模式枚举

        Raises:
            ValueError: 当模式值无效时抛出
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"无效的模式值 {value}")


class LLMUsage(ModelUsage):
    """
    LLM使用情况模型类

    记录大语言模型的详细使用统计信息
    """

    prompt_tokens: int  # 提示词标记数
    prompt_unit_price: Decimal  # 提示词单价
    prompt_price_unit: Decimal  # 提示词价格单位
    prompt_price: Decimal  # 提示词价格
    completion_tokens: int  # 完成标记数
    completion_unit_price: Decimal  # 完成单价
    completion_price_unit: Decimal  # 完成价格单位
    completion_price: Decimal  # 完成价格
    total_tokens: int  # 总标记数
    total_price: Decimal  # 总价格
    currency: str  # 货币类型
    latency: float  # 延迟时间

    @classmethod
    def empty_usage(cls):
        """
        创建空的使用情况实例

        Returns:
            LLMUsage: 初始化为0的使用情况实例
        """
        return cls(
            prompt_tokens=0,
            prompt_unit_price=Decimal("0.0"),
            prompt_price_unit=Decimal("0.0"),
            prompt_price=Decimal("0.0"),
            completion_tokens=0,
            completion_unit_price=Decimal("0.0"),
            completion_price_unit=Decimal("0.0"),
            completion_price=Decimal("0.0"),
            total_tokens=0,
            total_price=Decimal("0.0"),
            currency="USD",
            latency=0.0,
        )


class LLMResultChunkDelta(BaseModel):
    """
    LLM结果块增量模型类

    表示流式响应中的单个数据块增量
    """

    index: int  # 块索引
    message: AssistantPromptMessage  # 助手消息
    usage: LLMUsage | None = None  # 使用情况（可选）
    finish_reason: str | None = None  # 完成原因（可选）


class LLMResultChunk(BaseModel):
    """
    LLM结果块模型类

    表示流式响应中的单个数据块
    """

    model: str  # 模型名称
    prompt_messages: list[PromptMessage] = Field(default_factory=list)  # 提示消息列表
    system_fingerprint: str | None = None  # 系统指纹（可选）
    delta: LLMResultChunkDelta  # 增量数据

    @field_validator("prompt_messages", mode="before")
    @classmethod
    def transform_prompt_messages(cls, value):
        """
        转换提示消息字段

        问题参考:
        - https://github.com/langgenius/dify/issues/17799
        - https://github.com/langgenius/dify-official-plugins/issues/648

        `prompt_messages` 字段已废弃，但为了保持向后兼容性
        我们需要始终将其设置为空列表。

        注意: 请不要再使用此字段，将来会被删除。
        """
        return []


class LLMResult(BaseModel):
    """
    LLM结果模型类

    表示大语言模型的完整响应结果
    """

    model: str  # 模型名称
    prompt_messages: list[PromptMessage] = Field(default_factory=list)  # 提示消息列表
    message: AssistantPromptMessage  # 助手消息
    usage: LLMUsage  # 使用情况
    system_fingerprint: str | None = None  # 系统指纹（可选）

    @field_validator("prompt_messages", mode="before")
    @classmethod
    def transform_prompt_messages(cls, value):
        """
        转换提示消息字段

        问题参考:
        - https://github.com/langgenius/dify/issues/17799
        - https://github.com/langgenius/dify-official-plugins/issues/648

        `prompt_messages` 字段已废弃，但为了保持向后兼容性
        我们需要始终将其设置为空列表。

        注意: 请不要再使用此字段，将来会被删除。
        """
        return []

    def to_llm_result_chunk(self) -> "LLMResultChunk":
        """
        将LLM结果转换为结果块

        Returns:
            LLMResultChunk: 对应的结果块实例
        """
        return LLMResultChunk(
            model=self.model,
            system_fingerprint=self.system_fingerprint,
            delta=LLMResultChunkDelta(
                index=0,
                message=self.message,
                usage=self.usage,
                finish_reason=None,
            ),
        )


class SummaryResult(BaseModel):
    """
    摘要结果模型类

    用于存储文本摘要的结果
    """

    summary: str  # 摘要内容


class NumTokensResult(PriceInfo):
    """
    标记数结果模型类

    继承自价格信息，包含标记数统计
    """

    tokens: int  # 标记数量


class LLMModelConfig(BaseModelConfig):
    """
    LLM模型配置类

    继承自基础模型配置，专门用于大语言模型配置
    """

    model_type: ModelType = ModelType.LLM  # 模型类型，固定为LLM
    mode: str  # 运行模式
    completion_params: dict = Field(default_factory=dict)  # 完成参数字典

    model_config = ConfigDict(protected_namespaces=())
