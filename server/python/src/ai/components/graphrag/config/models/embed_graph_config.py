"""默认配置的参数设置."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs


class EmbedGraphConfig(BaseModel):
    """Node2Vec 的默认配置部分."""

    enabled: bool = Field(
        description="是否启用 node2vec 的标志。",
        default=defs.NODE2VEC_ENABLED,
    )
    num_walks: int = Field(
        description="node2vec 的游走次数。", default=defs.NODE2VEC_NUM_WALKS
    )
    walk_length: int = Field(
        description="node2vec 的游走长度。", default=defs.NODE2VEC_WALK_LENGTH
    )
    window_size: int = Field(
        description="node2vec 的窗口大小。", default=defs.NODE2VEC_WINDOW_SIZE
    )
    iterations: int = Field(
        description="node2vec 的迭代次数。", default=defs.NODE2VEC_ITERATIONS
    )
    random_seed: int = Field(
        description="node2vec 的随机种子。", default=defs.NODE2VEC_RANDOM_SEED
    )
    strategy: dict | None = Field(description="图嵌入策略覆盖。", default=None)

    def resolved_strategy(self) -> dict:
        """获取解析后的 node2vec 策略."""
        from ai.components.graphrag.index.verbs.graph.embed import (
            EmbedGraphStrategyType,
        )

        return self.strategy or {
            "type": EmbedGraphStrategyType.node2vec,
            "num_walks": self.num_walks,
            "walk_length": self.walk_length,
            "window_size": self.window_size,
            "iterations": self.iterations,
            "random_seed": self.iterations,
        }
