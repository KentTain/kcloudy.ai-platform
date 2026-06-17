"""PipelineStorage 的 MinIO S3 兼容实现."""

import logging
import re
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path
from typing import Any

from datashaper import Progress
from minio import Minio
from minio.error import S3Error

from ai.components.graphrag.index.progress import ProgressReporter
from ai.components.graphrag.index.storage.typing import PipelineStorage

log = logging.getLogger(__name__)


class MinioPipelineStorage(PipelineStorage):
    """MinIO S3 兼容存储实现."""

    _client: Minio
    _bucket_name: str
    _path_prefix: str
    _encoding: str
    _endpoint: str
    _access_key: str
    _secret_key: str
    _secure: bool
    _region: str | None
    _enable_virtual_style_endpoint: bool | None

    def __init__(
        self,
        endpoint: str | None,
        access_key: str | None,
        secret_key: str | None,
        bucket_name: str | None,
        secure: bool | None = None,
        region: str | None = None,
        encoding: str | None = None,
        path_prefix: str | None = None,
        enable_virtual_style_endpoint: bool | None = None,
    ):
        """创建新的 MinIO 存储实例."""
        if endpoint is None:
            msg = "No endpoint provided for MinIO storage."
            raise ValueError(msg)
        if access_key is None:
            msg = "No access key provided for MinIO storage."
            raise ValueError(msg)
        if secret_key is None:
            msg = "No secret key provided for MinIO storage."
            raise ValueError(msg)
        if bucket_name is None:
            msg = "No bucket name provided for MinIO storage."
            raise ValueError(msg)
        if secure is None:
            secure = True

        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._secure = secure
        self._region = region
        self._enable_virtual_style_endpoint = enable_virtual_style_endpoint

        self._client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )

        # 目前阿里云和腾讯云对象存储都只能是enable_virtual_style_endpoint访问方式, 而minio默认必须是disable_virtual_style_endpoint方式
        if enable_virtual_style_endpoint is None:
            if self._endpoint.endswith("aliyuncs.com") or self._endpoint.endswith(
                "myqcloud.com"
            ):
                self._client.enable_virtual_style_endpoint()
        elif enable_virtual_style_endpoint is True:
            self._client.enable_virtual_style_endpoint()
        elif enable_virtual_style_endpoint is False:
            self._client.disable_virtual_style_endpoint()

        self._bucket_name = bucket_name
        self._path_prefix = path_prefix or ""
        self._encoding = encoding or "utf-8"

        log.info(
            "creating MinIO storage at bucket=%s, path=%s",
            self._bucket_name,
            self._path_prefix,
        )
        self.create_bucket()

    def create_bucket(self) -> None:
        """如果桶不存在,则创建桶."""
        if not self.bucket_exists():
            try:
                self._client.make_bucket(self._bucket_name)
                log.info("Created bucket %s", self._bucket_name)
            except S3Error as e:
                if e.code == "BucketAlreadyOwnedByYou":
                    log.info("Bucket %s already exists", self._bucket_name)
                else:
                    raise

    def delete_bucket(self) -> None:
        """删除桶."""
        if self.bucket_exists():
            self._client.remove_bucket(self._bucket_name)

    def bucket_exists(self) -> bool:
        """检查桶是否存在."""
        # return self._client.bucket_exists(self._bucket_name)
        # 暂时先返回True,因为阿里云的桶判断方法需要更大的权限,暂时先不使用
        return True

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressReporter | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """
        使用文件模式和自定义过滤函数在桶中查找对象。

        Args:
            file_pattern: 用于匹配的文件模式。
            base_dir: 要搜索的基础目录。
            progress: 用于跟踪搜索进度的进度报告器。
            file_filter: 用于过滤对象的键值对字典。
            max_count: 要返回的最大对象数。如果为 -1,则返回所有对象。

        Returns
        -------
            对象名称及其对应正则匹配的迭代器。
        """
        base_dir = base_dir or ""
        prefix = str(Path(self._path_prefix) / base_dir).replace("\\", "/")
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        log.info(
            "search bucket %s for files matching %s with prefix %s",
            self._bucket_name,
            file_pattern.pattern,
            prefix,
        )

        def objectname(object_name: str) -> str:
            """通过删除前缀来清理对象名称."""
            if object_name.startswith(self._path_prefix):
                object_name = object_name.replace(self._path_prefix, "", 1)
            object_name = object_name.removeprefix("/")
            return object_name

        def item_filter(item: dict[str, Any]) -> bool:
            """对项目应用自定义过滤器."""
            if file_filter is None:
                return True
            return all(re.match(value, item[key]) for key, value in file_filter.items())

        try:
            # 列出具有给定前缀的所有对象
            all_objects = list(
                self._client.list_objects(
                    self._bucket_name, prefix=prefix, recursive=True
                )
            )

            num_loaded = 0
            num_total = len(all_objects)
            num_filtered = 0

            for obj in all_objects:
                object_name = obj.object_name
                if object_name is None:
                    continue

                match = file_pattern.match(object_name)
                if match:
                    group = match.groupdict()
                    if item_filter(group):
                        yield (objectname(object_name), group)
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

        except S3Error:
            log.exception(
                "Error finding objects: base_dir=%s, file_pattern=%s, file_filter=%s",
                base_dir,
                file_pattern,
                file_filter,
            )
            raise

    async def get(
        self, key: str, as_bytes: bool | None = False, encoding: str | None = None
    ) -> Any:
        """从桶中获取对象."""
        try:
            object_name = self._keyname(key)
            response = self._client.get_object(self._bucket_name, object_name)

            try:
                data = response.data
                if not as_bytes:
                    coding = encoding or self._encoding
                    data = data.decode(coding)
                return data
            finally:
                response.close()
                response.release_conn()

        except S3Error as e:
            if e.code == "NoSuchKey":
                log.debug("Object not found: %s", key)
                return None
            log.exception("Error getting object %s", key)
            return None
        except Exception:
            log.exception("Error getting object %s", key)
            return None

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """在桶中设置对象."""
        try:
            object_name = self._keyname(key)

            if isinstance(value, bytes):
                data = BytesIO(value)
                length = len(value)
            else:
                coding = encoding or self._encoding
                encoded_value = value.encode(coding)
                data = BytesIO(encoded_value)
                length = len(encoded_value)

            self._client.put_object(
                bucket_name=self._bucket_name,
                object_name=object_name,
                data=data,
                length=length,
            )

        except S3Error:
            log.exception("Error setting object %s", key)
            raise
        except Exception:
            log.exception("Error setting object %s", key)
            raise

    async def has(self, key: str) -> bool:
        """检查桶中是否存在对象."""
        try:
            object_name = self._keyname(key)
            self._client.stat_object(self._bucket_name, object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            log.exception("Error checking if object exists %s", key)
            return False
        except Exception:
            log.exception("Error checking if object exists %s", key)
            return False

    async def delete(self, key: str) -> None:
        """从桶中删除对象."""
        try:
            object_name = self._keyname(key)
            self._client.remove_object(self._bucket_name, object_name)
        except S3Error as e:
            if e.code != "NoSuchKey":
                log.exception("Error deleting object %s", key)
                raise
        except Exception:
            log.exception("Error deleting object %s", key)
            raise

    async def clear(self) -> None:
        """清空存储路径中的所有对象."""
        try:
            # 列出具有路径前缀的所有对象
            objects = self._client.list_objects(
                self._bucket_name, prefix=self._path_prefix, recursive=True
            )

            # 转换为 DeleteObject 列表以进行批量删除
            from minio.deleteobjects import DeleteObject

            delete_objects = [
                DeleteObject(obj.object_name)
                for obj in objects
                if obj.object_name is not None
            ]

            if delete_objects:
                # 使用批量删除以提高效率
                errors = self._client.remove_objects(self._bucket_name, delete_objects)
                for error in errors:
                    log.error("Error deleting object during clear: %s", error)

        except S3Error:
            log.exception("Error clearing storage")
            raise
        except Exception:
            log.exception("Error clearing storage")
            raise

    def child(self, name: str | None) -> "PipelineStorage":
        """创建子存储实例."""
        if name is None:
            return self

        path = str(Path(self._path_prefix) / name).replace("\\", "/")
        return MinioPipelineStorage(
            endpoint=self._endpoint,
            access_key=self._access_key,
            secret_key=self._secret_key,
            bucket_name=self._bucket_name,
            secure=self._secure,
            region=self._region,
            encoding=self._encoding,
            enable_virtual_style_endpoint=self._enable_virtual_style_endpoint,
            path_prefix=path,
        )

    def _keyname(self, key: str) -> str:
        """获取带路径前缀的完整对象名称."""
        return str(Path(self._path_prefix) / key).replace("\\", "/")


def create_minio_storage(
    endpoint: str,
    access_key: str,
    secret_key: str,
    bucket_name: str,
    secure: bool = True,
    region: str | None = None,
    base_dir: str | None = None,
    enable_virtual_style_endpoint: bool | None = None,
) -> PipelineStorage:
    """创建基于 MinIO 的存储."""
    log.info("Creating MinIO storage at %s/%s", endpoint, bucket_name)

    if not bucket_name:
        msg = "No bucket name provided for MinIO storage."
        raise ValueError(msg)
    if not endpoint:
        msg = "No endpoint provided for MinIO storage."
        raise ValueError(msg)
    if not access_key or not secret_key:
        msg = "No access key or secret key provided for MinIO storage."
        raise ValueError(msg)

    return MinioPipelineStorage(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket_name=bucket_name,
        secure=secure,
        region=region,
        path_prefix=base_dir,
        enable_virtual_style_endpoint=enable_virtual_style_endpoint,
    )


def validate_minio_bucket_name(bucket_name: str) -> bool:
    """
    验证 S3 兼容的桶名称。

    规则:
    - 长度必须在 3 到 63 个字符之间
    - 只能由小写字母,数字,点(.)和连字符(-)组成
    - 必须以字母或数字开头和结尾
    - 不能包含连续的点
    - 不能格式化为 IP 地址

    Args:
        bucket_name: 要验证的桶名称。

    Returns
    -------
        如果有效则为 True。

    Raises
    ------
        ValueError: 如果桶名称无效。
    """
    # 检查长度
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        raise ValueError(
            f"Bucket name must be between 3 and 63 characters long. "
            f"Provided name was {len(bucket_name)} characters long."
        )

    # 必须以字母或数字开头和结尾
    if not (bucket_name[0].isalnum() and bucket_name[-1].isalnum()):
        raise ValueError("Bucket name must start and end with a letter or number.")

    # 检查有效字符
    if not re.match(r"^[a-z0-9.-]+$", bucket_name):
        raise ValueError(
            "Bucket name can only contain lowercase letters, numbers, dots (.), and hyphens (-)."
        )

    # 没有连续的点
    if ".." in bucket_name:
        raise ValueError("Bucket name cannot contain consecutive periods.")

    # 不能格式化为 IP 地址
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", bucket_name):
        raise ValueError("Bucket name cannot be formatted as an IP address.")

    return True


def _create_progress_status(
    num_loaded: int, num_filtered: int, num_total: int
) -> Progress:
    """创建进度状态对象."""
    return Progress(
        total_items=num_total,
        completed_items=num_loaded + num_filtered,
        description=f"{num_loaded} files loaded ({num_filtered} filtered)",
    )
