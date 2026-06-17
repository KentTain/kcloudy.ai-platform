"""默认配置的参数设置."""

from pydantic import Field

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.enums import TextEmbeddingTarget
from ai.components.graphrag.config.models.llm_config import LLMConfig


class TextEmbeddingConfig(LLMConfig):
    """文本嵌入的配置部分."""

    batch_size: int = Field(
        description="要使用的批次大小。", default=defs.EMBEDDING_BATCH_SIZE
    )
    batch_max_tokens: int = Field(
        description="要使用的批次最大 token 数。",
        default=defs.EMBEDDING_BATCH_MAX_TOKENS,
    )
    target: TextEmbeddingTarget = Field(
        description="要使用的目标。'all' 或 'required'。",
        default=defs.EMBEDDING_TARGET,
    )
    skip: list[str] = Field(description="要跳过的特定嵌入。", default=[])
    vector_store: dict | None = Field(description="向量存储配置", default=None)
    strategy: dict | None = Field(description="要使用的覆盖策略。", default=None)

    def resolved_strategy(self) -> dict:
        """获取解析后的文本嵌入策略."""
        from ai.components.graphrag.index.verbs.text.embed import (
            TextEmbedStrategyType,
        )

        return self.strategy or {
            "type": TextEmbedStrategyType.openai,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "batch_size": self.batch_size,
            "batch_max_tokens": self.batch_max_tokens,
        }
