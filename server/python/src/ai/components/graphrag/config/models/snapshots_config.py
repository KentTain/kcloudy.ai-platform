"""默认配置的参数设置."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs


class SnapshotsConfig(BaseModel):
    """快照的配置部分."""

    graphml: bool = Field(
        description="是否对 GraphML 进行快照的标志。",
        default=defs.SNAPSHOTS_GRAPHML,
    )
    raw_entities: bool = Field(
        description="是否对原始实体进行快照的标志。",
        default=defs.SNAPSHOTS_RAW_ENTITIES,
    )
    top_level_nodes: bool = Field(
        description="是否对顶级节点进行快照的标志。",
        default=defs.SNAPSHOTS_TOP_LEVEL_NODES,
    )
