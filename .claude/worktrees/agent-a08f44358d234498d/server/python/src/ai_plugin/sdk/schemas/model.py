from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class ModelType(Enum):
    """
    模型类型枚举类

    定义系统支持的各种AI模型类型
    """

    LLM = "llm"  # 大语言模型
    TEXT_EMBEDDING = "text-embedding"  # 文本嵌入模型
    RERANK = "rerank"  # 重排序模型
    SPEECH2TEXT = "speech2text"  # 语音转文本模型
    MODERATION = "moderation"  # 内容审核模型
    TTS = "tts"  # 文本转语音模型

    @classmethod
    def value_of(cls, origin_model_type: str) -> "ModelType":
        """
        从原始模型类型获取ModelType枚举值

        :param origin_model_type: 原始模型类型字符串
        :return: 对应的ModelType枚举值
        :raises ValueError: 当原始模型类型无效时抛出异常
        """
        if origin_model_type in {"text-generation", cls.LLM.value}:
            return cls.LLM
        elif origin_model_type in {"embeddings", cls.TEXT_EMBEDDING.value}:
            return cls.TEXT_EMBEDDING
        elif origin_model_type in {"reranking", cls.RERANK.value}:
            return cls.RERANK
        elif origin_model_type in {"speech2text", cls.SPEECH2TEXT.value}:
            return cls.SPEECH2TEXT
        elif origin_model_type in {"tts", cls.TTS.value}:
            return cls.TTS
        elif origin_model_type == cls.MODERATION.value:
            return cls.MODERATION
        else:
            raise ValueError(f"无效的原始模型类型: {origin_model_type}")

    def to_origin_model_type(self) -> str:
        """
        将ModelType枚举值转换为原始模型类型字符串

        :return: 原始模型类型字符串
        :raises ValueError: 当模型类型无效时抛出异常
        """
        if self == self.LLM:
            return "text-generation"
        elif self == self.TEXT_EMBEDDING:
            return "embeddings"
        elif self == self.RERANK:
            return "reranking"
        elif self == self.SPEECH2TEXT:
            return "speech2text"
        elif self == self.TTS:
            return "tts"
        elif self == self.MODERATION:
            return "moderation"
        else:
            raise ValueError(f"无效的模型类型: {self}")


class ModelUsage(BaseModel):
    """
    模型使用统计基类

    用于记录模型使用的各种指标和统计信息
    """

    pass


class PriceType(Enum):
    """
    价格类型枚举类

    区分输入和输出的不同计费类型
    """

    INPUT = "input"  # 输入价格
    OUTPUT = "output"  # 输出价格


class PriceInfo(BaseModel):
    """
    价格信息模型类

    记录模型使用的详细价格信息
    """

    unit_price: Decimal  # 单价
    unit: Decimal  # 计价单位
    total_amount: Decimal  # 总金额
    currency: str  # 货币类型
