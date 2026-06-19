"""存储管理模块。

Storage management module.
"""

import logging
from pathlib import Path

from ai.components.graphrag.config.enums import InputType
from ai.components.graphrag.config.models.input_config import InputConfig
from ai.components.graphrag.index.config.input import PipelineInputConfig
from ai.components.graphrag.index.progress.types import (
    NullProgressReporter,
    PrintProgressReporter,
    ProgressReporter,
)
from ai.components.graphrag.index.storage import FilePipelineStorage
from ai.components.graphrag.index.storage.minio_pipeline_storage import (
    MinioPipelineStorage,
)
from ai.components.graphrag.index.storage.typing import PipelineStorage
from ai.components.graphrag.prompt_tune.loader.config import read_config_parameters
from ai.components.graphrag.webserver.utils.consts import RAGCONFIG_PATH
from ai.components.graphrag.webserver.utils.rag_util import (
    build_path_prefix,
    build_root_path,
)

_logger = logging.getLogger(__name__)


class Storage:
    """
    存储管理类,支持多种存储类型(文件,Blob,MinIO)。

    Storage management class supporting multiple storage types (file, blob, MinIO).
    """

    def __init__(self, namespace: str, code: str, filename: str):
        """
        初始化存储管理器。

        Initialize storage manager.

        参数 Parameters
        ----------
        namespace : str
            命名空间。Namespace.
        code : str
            代码标识。Code identifier.
        filename : str
            文件名。Filename.
        """
        self.path_prefix = build_path_prefix(namespace, code, filename)

        root_dir = build_root_path(namespace, code, filename)
        config_dir = RAGCONFIG_PATH

        reporter = PrintProgressReporter("Storage->")
        self.graph_config = read_config_parameters(root_dir, reporter, config_dir)
        self.storage = self.storage_init(
            config=self.graph_config.input,
            progress_reporter=reporter,
            root_dir=root_dir,
        )

    def storage_init(
        self,
        config: PipelineInputConfig | InputConfig,
        progress_reporter: ProgressReporter | None = None,
        root_dir: str | None = None,
    ) -> PipelineStorage:
        """
        初始化存储实例。

        Load the input data for a pipeline.

        参数 Parameters
        ----------
        config : PipelineInputConfig | InputConfig
            存储配置。Storage configuration.
        progress_reporter : ProgressReporter | None
            进度报告器。Progress reporter.
        root_dir : str | None
            根目录。Root directory.

        返回 Returns
        -------
        PipelineStorage
            初始化的存储实例。Initialized storage instance.
        """
        root_dir = root_dir or ""
        _logger.info("正在初始化存储, root_dir=%s", config.base_dir)
        progress_reporter = progress_reporter or NullProgressReporter()

        if config is None:
            msg = "未指定输入!"
            raise ValueError(msg)
        if config.base_dir is None:
            config.base_dir = ""

        match config.type:
            case InputType.blob:
                _logger.info("使用blob存储")
                if config.container_name is None:
                    msg = "blob存储需要指定容器名称"
                    raise ValueError(msg)
                if (
                    config.connection_string is None
                    and config.storage_account_blob_url is None
                ):
                    msg = "blob存储需要指定连接字符串或存储账户blob url"
                    raise ValueError(msg)
                # 延迟导入 BlobPipelineStorage
                from ai.components.graphrag.index.storage.blob_pipeline_storage import (
                    BlobPipelineStorage,
                )

                storage = BlobPipelineStorage(
                    connection_string=config.connection_string,
                    storage_account_blob_url=config.storage_account_blob_url,
                    container_name=config.container_name,
                    path_prefix=self.path_prefix + "/" + config.base_dir,
                )

            case InputType.minio:
                _logger.info("使用minio存储")

                storage = MinioPipelineStorage(
                    endpoint=config.endpoint,
                    access_key=config.access_key,
                    secret_key=config.secret_key,
                    bucket_name=config.container_name,
                    secure=config.secure,
                    region=config.region,
                    path_prefix=self.path_prefix + "/" + config.base_dir,
                )
            case InputType.file:
                _logger.info("使用文件存储")
                storage = FilePipelineStorage(
                    root_dir=str(Path(root_dir) / (config.base_dir or ""))
                )
            case _:
                _logger.info("使用文件存储2")
                storage = FilePipelineStorage(
                    root_dir=str(Path(root_dir) / (config.base_dir or ""))
                )

        return storage

    def upload(self, filename: str, file_path: str):
        """
        上传文件到存储。

        Upload file to storage.

        参数 Parameters
        ----------
        filename : str
            目标文件名。Target filename.
        file_path : str
            本地文件路径。Local file path.
        """
        with open(file_path, "rb") as f:
            self.storage.set(filename, f.read())

    def exists(self, filename: str):
        """
        检查文件是否存在。

        Check if file exists.

        参数 Parameters
        ----------
        filename : str
            文件名。Filename.

        返回 Returns
        -------
        bool
            文件是否存在。Whether file exists.
        """
        exists = self.storage.has(filename)
        return exists
