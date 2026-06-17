"""包含 load_storage 方法定义的模块."""

from __future__ import annotations

from typing import cast

from ai.components.graphrag.config import StorageType
from ai.components.graphrag.index.config.storage import (
    PipelineBlobStorageConfig,
    PipelineFileStorageConfig,
    PipelineMinioStorageConfig,
    PipelineStorageConfig,
)
from ai.components.graphrag.index.storage.file_pipeline_storage import (
    create_file_storage,
)
from ai.components.graphrag.index.storage.memory_pipeline_storage import (
    create_memory_storage,
)
from ai.components.graphrag.index.storage.minio_pipeline_storage import (
    create_minio_storage,
)


def load_storage(config: PipelineStorageConfig, root_dir: str | None = None):
    """加载管道的存储."""
    print(f"StorageType type: {config.type}")

    path_prefix = ""

    if root_dir is not None:
        from ai.components.graphrag.webserver.utils.rag_util import (
            build_minio_path_prefix,
        )

        path_prefix = build_minio_path_prefix(root_dir)

    match config.type:
        case StorageType.memory:
            return create_memory_storage()
        case StorageType.blob:
            config = cast("PipelineBlobStorageConfig", config)
            # 延迟导入 create_blob_storage
            from ai.components.graphrag.index.storage.blob_pipeline_storage import (
                create_blob_storage,
            )

            return create_blob_storage(
                config.connection_string,
                config.storage_account_blob_url,
                config.container_name,
                config.base_dir,
            )
        case StorageType.file:
            config = cast("PipelineFileStorageConfig", config)
            return create_file_storage(config.base_dir)
        case StorageType.minio:
            config = cast("PipelineMinioStorageConfig", config)
            if config.base_dir is None:
                raise ValueError("base_dir is None")

            return create_minio_storage(
                endpoint=config.endpoint,
                access_key=config.access_key,
                secret_key=config.secret_key,
                bucket_name=config.container_name,
                secure=config.secure,
                region=config.region,
                base_dir=path_prefix + "/" + config.base_dir,
                enable_virtual_style_endpoint=config.enable_virtual_style_endpoint,
            )
        case _:
            msg = f"Unknown storage type: {config.type}"
            raise ValueError(msg)
