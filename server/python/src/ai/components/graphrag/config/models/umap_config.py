"""默认配置的参数设置."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs


class UmapConfig(BaseModel):
    """UMAP 的配置部分."""

    enabled: bool = Field(
        description="是否启用 UMAP 的标志。",
        default=defs.UMAP_ENABLED,
    )
