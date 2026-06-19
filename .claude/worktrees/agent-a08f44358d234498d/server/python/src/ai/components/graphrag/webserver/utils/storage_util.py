"""提供图谱检索增强生成工具相关功能。"""

import asyncio
import enum
import logging
from pathlib import Path

from ai.components.graphrag.config.enums import InputType
from ai.components.graphrag.config.models.input_config import InputConfig
from ai.components.graphrag.config.models.storage_config import StorageConfig
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
    build_minio_path_prefix,
    build_root_path,
)

_logger = logging.getLogger(__name__)


class ConfigType(str, enum.Enum):
    """封装图谱检索增强生成工具中的ConfigType逻辑。"""

    input = "input"
    """The input type."""
    storage = "storage"
    """The storage type."""


class StorageObject:
    """封装图谱检索增强生成工具中的StorageObject逻辑。"""

    def __init__(
        self,
        namespace: str,
        code: str,
        filename: str,
        config_type: ConfigType,
    ):
        """
        初始化实例。

        Args:
            namespace (str): namespace 参数。
            code (str): code 参数。
            filename (str): filename 参数。
            config_type (ConfigType): config_type 参数。
        """
        root_dir = build_root_path(namespace, code, filename)
        config_dir = RAGCONFIG_PATH

        reporter = PrintProgressReporter("Storage->")
        self.graph_config = read_config_parameters(root_dir, reporter, config_dir)

        if config_type == ConfigType.input:
            config = self.graph_config.input
        elif config_type == ConfigType.storage:
            config = self.graph_config.storage
        else:
            raise ValueError(f"Invalid config type: {config_type}")

        self.storage = self.storage_init(
            config=config,
            progress_reporter=reporter,
            root_dir=root_dir,
        )

    def storage_init(
        self,
        config: PipelineInputConfig | InputConfig | StorageConfig,
        progress_reporter: ProgressReporter | None = None,
        root_dir: str | None = None,
    ) -> PipelineStorage:
        """
        处理storage_init。

        Args:
            config (PipelineInputConfig | InputConfig | StorageConfig): config 参数。
            progress_reporter (ProgressReporter | None): progress_reporter 参数。
            root_dir (str | None): root_dir 参数。

        Returns:
            处理结果。
        """
        _logger.info(
            "正在初始化存储, root_dir=%s, base_dir=%s", root_dir, config.base_dir
        )

        if config is None:
            msg = "未指定输入!"
            raise ValueError(msg)
        if config.base_dir is None:
            raise ValueError("base_dir is None")
        if root_dir is None:
            raise ValueError("root_dir is None")

        path_prefix = build_minio_path_prefix(root_dir)
        progress_reporter = progress_reporter or NullProgressReporter()

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
                    path_prefix=path_prefix + "/" + config.base_dir,
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
                    path_prefix=path_prefix + "/" + config.base_dir,
                    enable_virtual_style_endpoint=config.enable_virtual_style_endpoint,
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

    def _run_async_in_sync(self, coro):
        """在同步上下文中运行异步协程"""
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行的事件循环,直接运行
            return asyncio.run(coro)

        # 有运行中的事件循环,使用线程池执行
        import threading

        result = None
        exception = None

        def run_in_thread():
            """执行in_thread。"""
            nonlocal result, exception
            try:
                # 在新线程中创建新的事件循环
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result = new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
            except Exception as e:
                exception = e

        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()

        if exception:
            raise exception
        return result

    def upload(self, filename: str, file_path: str):
        """上传文件."""
        with open(file_path, "rb") as f:
            data = f.read()

        # 在同步方法中运行异步操作
        self._run_async_in_sync(self.storage.set(filename, data))

    def exists(self, filename: str):
        """判断文件是否存在."""
        return self._run_async_in_sync(self.storage.has(filename))

    def get(
        self, filename: str, as_bytes: bool | None = None, encoding: str | None = None
    ):
        """获取文件内容."""
        return self._run_async_in_sync(self.storage.get(filename, as_bytes, encoding))
