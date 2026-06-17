"""默认配置的参数设置."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs


class ClusterGraphConfig(BaseModel):
    """图聚类的配置部分."""

    max_cluster_size: int = Field(
        description="要使用的最大聚类大小。", default=defs.MAX_CLUSTER_SIZE
    )
    strategy: dict | None = Field(description="要使用的聚类策略。", default=None)

    def resolved_strategy(self) -> dict:
        """获取解析后的聚类策略."""
        from ai.components.graphrag.index.verbs.graph.clustering import (
            GraphCommunityStrategyType,
        )

        return self.strategy or {
            "type": GraphCommunityStrategyType.leiden,
            "max_cluster_size": self.max_cluster_size,
        }
