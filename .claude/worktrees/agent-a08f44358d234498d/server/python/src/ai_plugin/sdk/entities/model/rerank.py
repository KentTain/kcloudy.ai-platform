from pydantic import BaseModel, ConfigDict

from ai_plugin.sdk.entities.model import BaseModelConfig, ModelType


class RerankDocument(BaseModel):
    """
    重排序文档模型类

    表示重排序结果中的单个文档
    """

    index: int  # 文档索引
    text: str  # 文档文本内容
    score: float  # 相关性得分


class RerankResult(BaseModel):
    """
    重排序结果模型类

    表示重排序模型的输出结果
    """

    model: str  # 模型名称
    docs: list[RerankDocument]  # 重排序后的文档列表


class RerankModelConfig(BaseModelConfig):
    """
    重排序模型配置类

    继承自基础模型配置，专门用于重排序模型配置
    """

    model_type: ModelType = ModelType.RERANK  # 模型类型，固定为重排序
    score_threshold: float  # 得分阈值
    top_n: int  # 返回文档数量

    model_config = ConfigDict(protected_namespaces=())
