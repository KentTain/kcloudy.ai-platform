"""包含load_cache方法定义的模块."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ai.components.graphrag.config.enums import CacheType
from ai.components.graphrag.index.config.cache import (
    PipelineBlobCacheConfig,
    PipelineFileCacheConfig,
    PipelineMinioCacheConfig,
)
from ai.components.graphrag.index.storage import FilePipelineStorage
from ai.components.graphrag.index.storage.minio_pipeline_storage import (
    MinioPipelineStorage,
)

if TYPE_CHECKING:
    from ai.components.graphrag.index.config import (
        PipelineCacheConfig,
    )

from ai.components.graphrag.index.cache.json_pipeline_cache import JsonPipelineCache
from ai.components.graphrag.index.cache.memory_pipeline_cache import (
    create_memory_cache,
)
from ai.components.graphrag.index.cache.noop_pipeline_cache import NoopPipelineCache


def load_cache(config: PipelineCacheConfig | None, root_dir: str | None):
    """从给定配置加载缓存."""
    if config is None:
        return NoopPipelineCache()

    path_prefix = ""

    if root_dir is not None:
        from ai.components.graphrag.webserver.utils.rag_util import (
            build_minio_path_prefix,
        )

        path_prefix = build_minio_path_prefix(root_dir)

    match config.type:
        case CacheType.none:
            return NoopPipelineCache()
        case CacheType.memory:
            return create_memory_cache()
        case CacheType.file:
            config = cast("PipelineFileCacheConfig", config)
            storage = FilePipelineStorage(root_dir).child(config.base_dir)
            return JsonPipelineCache(storage)
        case CacheType.blob:
            config = cast("PipelineBlobCacheConfig", config)
            # 延迟导入 BlobPipelineStorage
            from ai.components.graphrag.index.storage.blob_pipeline_storage import (
                BlobPipelineStorage,
            )

            storage = BlobPipelineStorage(
                config.connection_string,
                config.container_name,
                storage_account_blob_url=config.storage_account_blob_url,
            ).child(config.base_dir)
            return JsonPipelineCache(storage)
        case CacheType.minio:
            config = cast("PipelineMinioCacheConfig", config)
            if config.base_dir is None:
                raise ValueError("base_dir is None")

            storage = MinioPipelineStorage(
                endpoint=config.endpoint,
                access_key=config.access_key,
                secret_key=config.secret_key,
                bucket_name=config.container_name,
                secure=config.secure,
                region=config.region,
                enable_virtual_style_endpoint=config.enable_virtual_style_endpoint,
            ).child(path_prefix + "/" + config.base_dir)
            return JsonPipelineCache(storage)
        case _:
            msg = f"Unknown cache type: {config.type}"
            raise ValueError(msg)
