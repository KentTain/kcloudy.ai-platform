"""默认配置的参数设置."""

from devtools import pformat
from pydantic import Field

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.models.cache_config import CacheConfig
from ai.components.graphrag.config.models.chunking_config import ChunkingConfig
from ai.components.graphrag.config.models.claim_extraction_config import (
    ClaimExtractionConfig,
)
from ai.components.graphrag.config.models.cluster_graph_config import (
    ClusterGraphConfig,
)
from ai.components.graphrag.config.models.community_reports_config import (
    CommunityReportsConfig,
)
from ai.components.graphrag.config.models.embed_graph_config import EmbedGraphConfig
from ai.components.graphrag.config.models.entity_extraction_config import (
    EntityExtractionConfig,
)
from ai.components.graphrag.config.models.global_search_config import (
    GlobalSearchConfig,
)
from ai.components.graphrag.config.models.input_config import InputConfig
from ai.components.graphrag.config.models.llm_config import LLMConfig
from ai.components.graphrag.config.models.local_search_config import LocalSearchConfig
from ai.components.graphrag.config.models.oss_config import OssConfig
from ai.components.graphrag.config.models.reporting_config import ReportingConfig
from ai.components.graphrag.config.models.reranker_config import RerankerConfig
from ai.components.graphrag.config.models.snapshots_config import SnapshotsConfig
from ai.components.graphrag.config.models.storage_config import StorageConfig
from ai.components.graphrag.config.models.summarize_descriptions_config import (
    SummarizeDescriptionsConfig,
)
from ai.components.graphrag.config.models.text_embedding_config import (
    TextEmbeddingConfig,
)
from ai.components.graphrag.config.models.umap_config import UmapConfig


class GraphRagConfig(LLMConfig):
    """默认配置参数化设置的基类."""

    def __repr__(self) -> str:
        """获取字符串表示."""
        return pformat(self, highlight=False)

    def __str__(self):
        """获取字符串表示."""
        return self.model_dump_json(indent=4)

    root_dir: str = Field(description="配置的根目录。", default=None)

    reporting: ReportingConfig = Field(
        description="报告配置。", default=ReportingConfig()
    )
    """报告配置."""

    storage: StorageConfig = Field(description="存储配置。", default=StorageConfig())
    """存储配置."""

    cache: CacheConfig = Field(description="缓存配置。", default=CacheConfig())
    """缓存配置."""

    input: InputConfig = Field(description="输入配置。", default=InputConfig())
    """输入配置."""

    embed_graph: EmbedGraphConfig = Field(
        description="图嵌入配置。",
        default=EmbedGraphConfig(),
    )
    """图嵌入配置."""

    embeddings: TextEmbeddingConfig = Field(
        description="要使用的嵌入 LLM 配置。",
        default=TextEmbeddingConfig(),
    )
    """要使用的嵌入 LLM 配置."""

    chunks: ChunkingConfig = Field(
        description="要使用的分块配置。",
        default=ChunkingConfig(),
    )
    """要使用的分块配置."""

    snapshots: SnapshotsConfig = Field(
        description="要使用的快照配置。",
        default=SnapshotsConfig(),
    )
    """要使用的快照配置."""

    entity_extraction: EntityExtractionConfig = Field(
        description="要使用的实体提取配置。",
        default=EntityExtractionConfig(),
    )
    """要使用的实体提取配置."""

    summarize_descriptions: SummarizeDescriptionsConfig = Field(
        description="要使用的描述摘要配置。",
        default=SummarizeDescriptionsConfig(),
    )
    """要使用的描述摘要配置."""

    community_reports: CommunityReportsConfig = Field(
        description="要使用的社区报告配置。",
        default=CommunityReportsConfig(),
    )
    """要使用的社区报告配置."""

    claim_extraction: ClaimExtractionConfig = Field(
        description="要使用的声明提取配置。",
        default=ClaimExtractionConfig(
            enabled=defs.CLAIM_EXTRACTION_ENABLED,
        ),
    )
    """要使用的声明提取配置."""

    cluster_graph: ClusterGraphConfig = Field(
        description="要使用的聚类图配置。",
        default=ClusterGraphConfig(),
    )
    """要使用的聚类图配置."""

    umap: UmapConfig = Field(description="要使用的 UMAP 配置。", default=UmapConfig())
    """要使用的 UMAP 配置."""

    local_search: LocalSearchConfig = Field(
        description="本地搜索配置。", default=LocalSearchConfig()
    )
    """本地搜索配置."""

    global_search: GlobalSearchConfig = Field(
        description="全局搜索配置。", default=GlobalSearchConfig()
    )
    """全局搜索配置."""

    encoding_model: str = Field(
        description="要使用的编码模型。", default=defs.ENCODING_MODEL
    )
    """要使用的编码模型."""

    skip_workflows: list[str] = Field(
        description="要跳过的工作流，通常用于测试目的。", default=[]
    )
    """要跳过的工作流,通常用于测试目的."""

    reranker: RerankerConfig = Field(
        description="reranker 配置。", default=RerankerConfig()
    )
    """reranker 配置."""

    os: OssConfig = Field(description="要使用的 OSS。", default=OssConfig())
    """要使用的 OS."""
