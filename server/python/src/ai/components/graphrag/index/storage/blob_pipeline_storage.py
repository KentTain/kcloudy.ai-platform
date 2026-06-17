"""PipelineStorage 的 Azure Blob 存储实现."""

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from datashaper import Progress

from ai.components.graphrag.index.progress import ProgressReporter
from ai.components.graphrag.index.storage.typing import PipelineStorage

log = logging.getLogger(__name__)


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


class BlobPipelineStorage(PipelineStorage):
    """Blob 存储实现."""

    _connection_string: str | None
    _container_name: str
    _path_prefix: str
    _encoding: str
    _storage_account_blob_url: str | None

    def __init__(
        self,
        connection_string: str | None,
        container_name: str,
        encoding: str | None = None,
        path_prefix: str | None = None,
        storage_account_blob_url: str | None = None,
    ):
        """创建新的 BlobStorage 实例."""
        # 延迟导入 Azure 依赖
        DefaultAzureCredential, BlobServiceClient = _get_azure_deps()

        if connection_string:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
        else:
            if storage_account_blob_url is None:
                msg = "Either connection_string or storage_account_blob_url must be provided."
                raise ValueError(msg)

            self._blob_service_client = BlobServiceClient(
                account_url=storage_account_blob_url,
                credential=DefaultAzureCredential(),
            )
        self._encoding = encoding or "utf-8"
        self._container_name = container_name
        self._connection_string = connection_string
        self._path_prefix = path_prefix or ""
        self._storage_account_blob_url = storage_account_blob_url
        self._storage_account_name = (
            storage_account_blob_url.split("//")[1].split(".")[0]
            if storage_account_blob_url
            else None
        )
        log.info(
            "creating blob storage at container=%s, path=%s",
            self._container_name,
            self._path_prefix,
        )
        self.create_container()

    def create_container(self) -> None:
        """如果容器不存在,则创建容器."""
        if not self.container_exists():
            container_name = self._container_name
            container_names = [
                container.name
                for container in self._blob_service_client.list_containers()
            ]
            if container_name not in container_names:
                self._blob_service_client.create_container(container_name)

    def delete_container(self) -> None:
        """删除容器."""
        if self.container_exists():
            self._blob_service_client.delete_container(self._container_name)

    def container_exists(self) -> bool:
        """检查容器是否存在."""
        container_name = self._container_name
        container_names = [
            container.name for container in self._blob_service_client.list_containers()
        ]
        return container_name in container_names

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressReporter | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """
        使用文件模式和自定义过滤函数在容器中查找 blob。

        Params:
            base_dir: 基础容器的名称。
            file_pattern: 要使用的文件模式。
            file_filter: 用于过滤 blob 的键值对字典。
            max_count: 要返回的最大 blob 数。如果为 -1,则返回所有 blob。

        Returns
        -------
                blob 名称及其对应正则匹配的迭代器。
        """
        base_dir = base_dir or ""

        log.info(
            "search container %s for files matching %s",
            self._container_name,
            file_pattern.pattern,
        )

        def blobname(blob_name: str) -> str:
            """
            处理blobname。

            Args:
                blob_name (str): blob_name 参数。

            Returns:
                处理结果。
            """
            if blob_name.startswith(self._path_prefix):
                blob_name = blob_name.replace(self._path_prefix, "", 1)
            blob_name = blob_name.removeprefix("/")
            return blob_name

        def item_filter(item: dict[str, Any]) -> bool:
            """
            处理item_filter。

            Args:
                item (dict[str, Any]): item 参数。

            Returns:
                处理结果。
            """
            if file_filter is None:
                return True

            return all(re.match(value, item[key]) for key, value in file_filter.items())

        try:
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            all_blobs = list(container_client.list_blobs())

            num_loaded = 0
            num_total = len(list(all_blobs))
            num_filtered = 0
            for blob in all_blobs:
                match = file_pattern.match(blob.name)
                if match and blob.name.startswith(base_dir):
                    group = match.groupdict()
                    if item_filter(group):
                        yield (blobname(blob.name), group)
                        num_loaded += 1
                        if max_count > 0 and num_loaded >= max_count:
                            break
                    else:
                        num_filtered += 1
                else:
                    num_filtered += 1
                if progress is not None:
                    progress(
                        _create_progress_status(num_loaded, num_filtered, num_total)
                    )
        except Exception:
            log.exception(
                "Error finding blobs: base_dir=%s, file_pattern=%s, file_filter=%s",
                base_dir,
                file_pattern,
                file_filter,
            )
            raise

    async def get(
        self, key: str, as_bytes: bool | None = False, encoding: str | None = None
    ) -> Any:
        """从缓存中获取值."""
        try:
            key = self._keyname(key)
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            blob_client = container_client.get_blob_client(key)
            blob_data = blob_client.download_blob().readall()
            if not as_bytes:
                coding = encoding or "utf-8"
                blob_data = blob_data.decode(coding)
        except Exception:
            log.exception("Error getting key %s", key)
            return None
        else:
            return blob_data

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """在缓存中设置值."""
        try:
            key = self._keyname(key)
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            blob_client = container_client.get_blob_client(key)
            if isinstance(value, bytes):
                blob_client.upload_blob(value, overwrite=True)
            else:
                coding = encoding or "utf-8"
                blob_client.upload_blob(value.encode(coding), overwrite=True)
        except Exception:
            log.exception("Error setting key %s: %s", key)

    def set_df_json(self, key: str, dataframe: Any) -> None:
        """设置 JSON 数据框."""
        # 延迟导入 Azure 依赖
        DefaultAzureCredential, _ = _get_azure_deps()

        if self._connection_string is None and self._storage_account_name:
            dataframe.to_json(
                self._abfs_url(key),
                storage_options={
                    "account_name": self._storage_account_name,
                    "credential": DefaultAzureCredential(),
                },
                orient="records",
                lines=True,
                force_ascii=False,
            )
        else:
            dataframe.to_json(
                self._abfs_url(key),
                storage_options={"connection_string": self._connection_string},
                orient="records",
                lines=True,
                force_ascii=False,
            )

    def set_df_parquet(self, key: str, dataframe: Any) -> None:
        """设置 parquet 数据框."""
        # 延迟导入 Azure 依赖
        DefaultAzureCredential, _ = _get_azure_deps()

        if self._connection_string is None and self._storage_account_name:
            dataframe.to_parquet(
                self._abfs_url(key),
                storage_options={
                    "account_name": self._storage_account_name,
                    "credential": DefaultAzureCredential(),
                },
            )
        else:
            dataframe.to_parquet(
                self._abfs_url(key),
                storage_options={"connection_string": self._connection_string},
            )

    async def has(self, key: str) -> bool:
        """检查缓存中是否存在键."""
        key = self._keyname(key)
        container_client = self._blob_service_client.get_container_client(
            self._container_name
        )
        blob_client = container_client.get_blob_client(key)
        return blob_client.exists()

    async def delete(self, key: str) -> None:
        """从缓存中删除键."""
        key = self._keyname(key)
        container_client = self._blob_service_client.get_container_client(
            self._container_name
        )
        blob_client = container_client.get_blob_client(key)
        blob_client.delete_blob()

    async def clear(self) -> None:
        """清空缓存."""

    def child(self, name: str | None) -> "PipelineStorage":
        """创建子存储实例."""
        if name is None:
            return self
        path = str(Path(self._path_prefix) / name)
        return BlobPipelineStorage(
            self._connection_string,
            self._container_name,
            self._encoding,
            path,
            self._storage_account_blob_url,
        )

    def _keyname(self, key: str) -> str:
        """获取键名."""
        return str(Path(self._path_prefix) / key)

    def _abfs_url(self, key: str) -> str:
        """获取 ABFS URL."""
        path = str(Path(self._container_name) / self._path_prefix / key)
        return f"abfs://{path}"


def create_blob_storage(
    connection_string: str | None,
    storage_account_blob_url: str | None,
    container_name: str,
    base_dir: str | None,
) -> PipelineStorage:
    """创建基于 blob 的存储."""
    log.info("Creating blob storage at %s", container_name)
    if container_name is None:
        msg = "No container name provided for blob storage."
        raise ValueError(msg)
    if connection_string is None and storage_account_blob_url is None:
        msg = "No storage account blob url provided for blob storage."
        raise ValueError(msg)
    return BlobPipelineStorage(
        connection_string,
        container_name,
        path_prefix=base_dir,
        storage_account_blob_url=storage_account_blob_url,
    )


def validate_blob_container_name(container_name: str):
    """
    根据 Azure 规则检查提供的 blob 容器名称是否有效。

        - blob 容器名称的长度必须在 3 到 63 个字符之间。
        - 以字母或数字开头
        - blob 容器名称中使用的所有字母必须为小写。
        - 只能包含字母,数字或连字符。
        - 不允许连续的连字符。
        - 不能以连字符结尾。

    Args:
    -----
    container_name (str)
        要验证的 blob 容器名称。

    Returns
    -------
        bool: 如果有效则为 True,否则为 False。
    """
    # 检查名称的长度
    if len(container_name) < 3 or len(container_name) > 63:
        return ValueError(
            f"Container name must be between 3 and 63 characters in length. Name provided was {len(container_name)} characters long."
        )

    # 检查名称是否以字母或数字开头
    if not container_name[0].isalnum():
        return ValueError(
            f"Container name must start with a letter or number. Starting character was {container_name[0]}."
        )

    # 检查有效字符(字母,数字,连字符)和小写字母
    if not re.match("^[a-z0-9-]+$", container_name):
        return ValueError(
            f"Container name must only contain:\n- lowercase letters\n- numbers\n- or hyphens\nName provided was {container_name}."
        )

    # 检查连续的连字符
    if "--" in container_name:
        return ValueError(
            f"Container name cannot contain consecutive hyphens. Name provided was {container_name}."
        )

    # 检查名称末尾的连字符
    if container_name[-1] == "-":
        return ValueError(
            f"Container name cannot end with a hyphen. Name provided was {container_name}."
        )

    return True


def _create_progress_status(
    num_loaded: int, num_filtered: int, num_total: int
) -> Progress:
    """
    创建progress_status。

    Args:
        num_loaded (int): num_loaded 参数。
        num_filtered (int): num_filtered 参数。
        num_total (int): num_total 参数。

    Returns:
        处理结果。
    """
    return Progress(
        total_items=num_total,
        completed_items=num_loaded + num_filtered,
        description=f"{num_loaded} files loaded ({num_filtered} filtered)",
    )
