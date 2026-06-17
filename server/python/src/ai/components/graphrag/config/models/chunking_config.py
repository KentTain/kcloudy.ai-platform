"""默认配置的参数设置."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs


class ChunkingConfig(BaseModel):
    """分块的配置部分."""

    size: int = Field(description="要使用的分块大小。", default=defs.CHUNK_SIZE)
    overlap: int = Field(description="要使用的分块重叠。", default=defs.CHUNK_OVERLAP)
    group_by_columns: list[str] = Field(
        description="要使用的分块列。",
        default=defs.CHUNK_GROUP_BY_COLUMNS,
    )
    strategy: dict | None = Field(
        description="要使用的分块策略，覆盖默认的标记化策略",
        default=None,
    )
    encoding_model: str | None = Field(default=None, description="要使用的编码模型。")

    def resolved_strategy(self, encoding_model: str) -> dict:
        """获取解析后的分块策略."""
        from ai.components.graphrag.index.verbs.text.chunk import ChunkStrategyType

        return self.strategy or {
            "type": ChunkStrategyType.tokens,
            "chunk_size": self.size,
            "chunk_overlap": self.overlap,
            "group_by_columns": self.group_by_columns,
            "encoding_name": self.encoding_model or encoding_model,
        }
