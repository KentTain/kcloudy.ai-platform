"""默认配置的参数设置."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs


class RerankerConfig(BaseModel):
    """重排序器的默认配置部分."""

    model: str = Field(
        description="重排序器模型。",
        default=defs.RERANKER_MODEL,
    )
    api_url: str | None = Field(description="重排序器 URL。", default=None)
    min_score: float = Field(
        description="重排序器最小分数。", default=defs.RERANKER_MIN_SCORE
    )
