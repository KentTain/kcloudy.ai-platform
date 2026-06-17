"""包含load_input方法定义的模块."""

import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import cast

import pandas as pd

from ai.components.graphrag.config import InputConfig, InputType
from ai.components.graphrag.index.config import PipelineInputConfig
from ai.components.graphrag.index.input.csv import input_type as csv
from ai.components.graphrag.index.input.csv import load as load_csv
from ai.components.graphrag.index.input.text import input_type as text
from ai.components.graphrag.index.input.text import load as load_text
from ai.components.graphrag.index.progress import (
    NullProgressReporter,
    ProgressReporter,
)
from ai.components.graphrag.index.storage import FilePipelineStorage
from ai.components.graphrag.index.storage.minio_pipeline_storage import (
    MinioPipelineStorage,
)

log = logging.getLogger(__name__)
loaders: dict[str, Callable[..., Awaitable[pd.DataFrame]]] = {
    text: load_text,
    csv: load_csv,
}


async def load_input(
    config: PipelineInputConfig | InputConfig,
    progress_reporter: ProgressReporter | None = None,
    root_dir: str | None = None,
) -> pd.DataFrame:
    """为管道加载输入数据."""
    root_dir = root_dir or ""
    log.info("loading input from root_dir=%s, base_dir=%s", root_dir, config.base_dir)

    if config is None:
        msg = "No input specified!"
        raise ValueError(msg)

    if config.base_dir is None:
        raise ValueError("base_dir is None")

    if root_dir is None:
        raise ValueError("root_dir is None")

    from ai.components.graphrag.webserver.utils.rag_util import (
        build_minio_path_prefix,
    )

    path_prefix = build_minio_path_prefix(root_dir)

    log.info("path_prefix=%s", path_prefix)

    progress_reporter = progress_reporter or NullProgressReporter()

    match config.type:
        case InputType.blob:
            log.info("using blob storage input")
            if config.container_name is None:
                msg = "Container name required for blob storage"
                raise ValueError(msg)
            if (
                config.connection_string is None
                and config.storage_account_blob_url is None
            ):
                msg = "Connection string or storage account blob url required for blob storage"
                raise ValueError(msg)
            # 延迟导入 BlobPipelineStorage
            from ai.components.graphrag.index.storage.blob_pipeline_storage import (
                BlobPipelineStorage,
            )

            storage = BlobPipelineStorage(
                connection_string=config.connection_string,
                storage_account_blob_url=config.storage_account_blob_url,
                container_name=config.container_name,
                path_prefix=path_prefix + "/" + config.base_dir,
            )
        case InputType.minio:
            log.info("using minio storage input")

            storage = MinioPipelineStorage(
                endpoint=config.endpoint,
                access_key=config.access_key,
                secret_key=config.secret_key,
                bucket_name=config.container_name,
                secure=config.secure,
                region=config.region,
                path_prefix=path_prefix + "/" + config.base_dir,
                enable_virtual_style_endpoint=config.enable_virtual_style_endpoint,
            )
        case InputType.file:
            log.info("using file storage for input")
            storage = FilePipelineStorage(
                root_dir=str(Path(root_dir) / (config.base_dir or ""))
            )
        case _:
            log.info("using file storage for input")
            storage = FilePipelineStorage(
                root_dir=str(Path(root_dir) / (config.base_dir or ""))
            )

    if config.file_type in loaders:
        progress = progress_reporter.child(
            f"Loading Input ({config.file_type})", transient=False
        )
        loader = loaders[config.file_type]
        results = await loader(config, progress, storage)
        return cast("pd.DataFrame", results)

    msg = f"Unknown input type {config.file_type}"
    raise ValueError(msg)
