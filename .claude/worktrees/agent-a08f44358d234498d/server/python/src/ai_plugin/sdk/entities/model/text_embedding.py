from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from ai_plugin.sdk.entities.model import BaseModelConfig, ModelType, ModelUsage


class EmbeddingUsage(ModelUsage):
    """
    文本嵌入使用情况模型类

    记录文本嵌入模型的使用统计信息
    """

    tokens: int  # 标记数量
    total_tokens: int  # 总标记数
    unit_price: Decimal  # 单价
    price_unit: Decimal  # 价格单位
    total_price: Decimal  # 总价格
    currency: str  # 货币类型
    latency: float  # 延迟时间


class TextEmbeddingResult(BaseModel):
    """
    文本嵌入结果模型类

    表示文本嵌入模型的输出结果
    """

    model: str  # 模型名称
    embeddings: list[list[float]]  # 嵌入向量列表
    usage: EmbeddingUsage  # 使用情况


class TextEmbeddingModelConfig(BaseModelConfig):
    """
    文本嵌入模型配置类

    继承自基础模型配置，专门用于文本嵌入模型配置
    """

    model_type: ModelType = ModelType.TEXT_EMBEDDING  # 模型类型，固定为文本嵌入

    model_config = ConfigDict(protected_namespaces=())
