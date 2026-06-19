from collections.abc import Sequence
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from ai_plugin.sdk.schemas.message import AssistantPromptMessage, PromptMessage
from ai_plugin.sdk.schemas.model import ModelUsage, PriceInfo


class LLMMode(StrEnum):
    """
    大语言模型模式枚举类

    定义LLM的不同工作模式
    """

    COMPLETION = "completion"  # 文本补全模式
    CHAT = "chat"  # 对话模式

    @classmethod
    def value_of(cls, value: str) -> "LLMMode":
        """
        根据字符串值获取对应的LLM模式

        :param value: 模式值字符串
        :return: 对应的LLMMode枚举值
        :raises ValueError: 当模式值无效时抛出异常
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"无效的 LLM 模式: {value}")


class LLMUsage(ModelUsage):
    """
    大语言模型使用统计类

    记录LLM使用的详细统计信息，包括token数量、价格、延迟等
    """

    prompt_tokens: int  # 提示词token数量
    prompt_unit_price: Decimal  # 提示词单价
    prompt_price_unit: Decimal  # 提示词计价单位
    prompt_price: Decimal  # 提示词总价格
    completion_tokens: int  # 生成内容token数量
    completion_unit_price: Decimal  # 生成内容单价
    completion_price_unit: Decimal  # 生成内容计价单位
    completion_price: Decimal  # 生成内容总价格
    total_tokens: int  # 总token数量
    total_price: Decimal  # 总价格
    currency: str  # 货币类型
    latency: float  # 延迟时间（秒）

    @classmethod
    def empty_usage(cls):
        """
        创建一个空的使用统计实例

        :return: 初始化为0的LLMUsage实例
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

    def plus(self, other: "LLMUsage") -> "LLMUsage":
        """
        将两个LLMUsage实例相加

        :param other: 另一个LLMUsage实例
        :return: 包含累计值的新LLMUsage实例
        """
        if self.total_tokens == 0:
            return other
        else:
            return LLMUsage(
                prompt_tokens=self.prompt_tokens + other.prompt_tokens,
                prompt_unit_price=other.prompt_unit_price,
                prompt_price_unit=other.prompt_price_unit,
                prompt_price=self.prompt_price + other.prompt_price,
                completion_tokens=self.completion_tokens + other.completion_tokens,
                completion_unit_price=other.completion_unit_price,
                completion_price_unit=other.completion_price_unit,
                completion_price=self.completion_price + other.completion_price,
                total_tokens=self.total_tokens + other.total_tokens,
                total_price=self.total_price + other.total_price,
                currency=other.currency,
                latency=self.latency + other.latency,
            )

    def __add__(self, other: "LLMUsage") -> "LLMUsage":
        """
        重载+运算符以支持两个LLMUsage实例相加

        :param other: 另一个LLMUsage实例
        :return: 包含累计值的新LLMUsage实例
        """
        return self.plus(other)


class LLMResult(BaseModel):
    """
    大语言模型响应结果类

    封装LLM调用的完整响应结果
    """

    id: str | None = None  # 响应ID
    model: str  # 使用的模型名称
    prompt_messages: Sequence[PromptMessage] = Field(default_factory=list)  # 输入的提示消息列表
    message: AssistantPromptMessage  # 生成的助手消息
    usage: LLMUsage  # 使用统计信息
    system_fingerprint: str | None = None  # 系统指纹


class LLMResultChunkDelta(BaseModel):
    """
    流式响应数据块增量类

    表示流式响应中的单个数据块变化
    """

    index: int  # 数据块索引
    message: AssistantPromptMessage  # 消息增量内容
    usage: LLMUsage | None = None  # 使用统计信息（可选）
    finish_reason: str | None = None  # 完成原因（可选）


class LLMResultChunk(BaseModel):
    """
    流式响应数据块类

    表示流式响应中的单个数据块
    """

    model: str  # 使用的模型名称
    prompt_messages: Sequence[PromptMessage] = Field(default_factory=list)  # 输入的提示消息列表
    system_fingerprint: str | None = None  # 系统指纹
    delta: LLMResultChunkDelta  # 数据块增量内容


class NumTokensResult(PriceInfo):
    """
    Token数量计算结果类

    继承自PriceInfo，包含token计数和价格信息
    """

    tokens: int  # token数量
