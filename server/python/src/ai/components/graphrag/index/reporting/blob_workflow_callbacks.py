"""向 blob 存储写入的报告器."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from datashaper import NoopWorkflowCallbacks

if TYPE_CHECKING:
    from azure.storage.blob import BlobServiceClient


def _get_azure_deps():
    """
    延迟导入 Azure 依赖.

    Lazily import Azure dependencies.
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        return DefaultAzureCredential, BlobServiceClient
    except ImportError as e:
        msg = "Azure Blob Storage 依赖未安装，请执行: pip install azure-identity azure-storage-blob"
        raise ImportError(msg) from e


class BlobWorkflowCallbacks(NoopWorkflowCallbacks):
    """向 blob 存储写入的报告器."""

    _blob_service_client: "BlobServiceClient"
    _container_name: str
    _max_block_count: int = 25000  # 每个 blob 25k 个块

    def __init__(
        self,
        connection_string: str | None,
        container_name: str,
        blob_name: str = "",
        base_dir: str | None = None,
        storage_account_blob_url: str | None = None,
    ):  # type: ignore
        """创建 BlobStorageReporter 类的新实例."""
        # 延迟导入 Azure 依赖
        DefaultAzureCredential, BlobServiceClient = _get_azure_deps()

        if container_name is None:
            msg = "No container name provided for blob storage."
            raise ValueError(msg)
        if connection_string is None and storage_account_blob_url is None:
            msg = "No storage account blob url provided for blob storage."
            raise ValueError(msg)
        self._connection_string = connection_string
        self._storage_account_blob_url = storage_account_blob_url
        if self._connection_string:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                self._connection_string
            )
        else:
            if storage_account_blob_url is None:
                msg = "Either connection_string or storage_account_blob_url must be provided."
                raise ValueError(msg)

            self._blob_service_client = BlobServiceClient(
                storage_account_blob_url,
                credential=DefaultAzureCredential(),
            )

        if blob_name == "":
            blob_name = f"report/{datetime.now(tz=UTC).strftime('%Y-%m-%d-%H:%M:%S:%f')}.logs.json"

        self._blob_name = str(Path(base_dir or "") / blob_name)
        self._container_name = container_name
        self._blob_client = self._blob_service_client.get_blob_client(
            self._container_name, self._blob_name
        )
        if not self._blob_client.exists():
            self._blob_client.create_append_blob()

        self._num_blocks = 0  # 重置块计数器

    def _write_log(self, log: dict[str, Any]):
        # 当块数接近 25k 时创建新文件
        """
        写入write_log。

        Args:
            log (dict[str, Any]): log 参数。
        """
        if self._num_blocks >= self._max_block_count:  # 检查块数是否超过 25k
            self.__init__(
                self._connection_string,
                self._container_name,
                storage_account_blob_url=self._storage_account_blob_url,
            )

        blob_client = self._blob_service_client.get_blob_client(
            self._container_name, self._blob_name
        )
        blob_client.append_block(json.dumps(log, ensure_ascii=False) + "\n")

        # 更新 blob 的块计数
        self._num_blocks += 1

    def on_error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ):
        """报告错误."""
        self._write_log(
            {
                "type": "error",
                "data": message,
                "cause": str(cause),
                "stack": stack,
                "details": details,
            }
        )

    def on_warning(self, message: str, details: dict | None = None):
        """报告警告."""
        self._write_log({"type": "warning", "data": message, "details": details})

    def on_log(self, message: str, details: dict | None = None):
        """报告通用日志消息."""
        self._write_log({"type": "log", "data": message, "details": details})
