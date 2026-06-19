"""
MinIO 存储实现
"""

import io
from typing import Any

from minio import Minio
from minio.error import S3Error

from framework.configs.settings import MinioSettings


class MinioStorage:
    """MinIO 存储实现"""

    def __init__(self, config: MinioSettings):
        self._config = config
        self._client = Minio(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
        )

    async def upload(
        self,
        bucket: str,
        name: str,
        data: bytes,
        content_type: str | None = None
    ) -> str:
        """上传文件"""
        if content_type is None:
            content_type = "application/octet-stream"

        self._client.put_object(
            bucket_name=bucket,
            object_name=name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

        return f"{bucket}/{name}"

    async def download(self, bucket: str, name: str) -> bytes:
        """下载文件"""
        response = self._client.get_object(bucket, name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def delete(self, bucket: str, name: str) -> bool:
        """删除文件"""
        try:
            self._client.remove_object(bucket, name)
            return True
        except S3Error:
            return False

    async def exists(self, bucket: str, name: str) -> bool:
        """检查文件是否存在"""
        try:
            self._client.stat_object(bucket, name)
            return True
        except S3Error:
            return False

    async def get_presigned_url(
        self,
        bucket: str,
        name: str,
        expires: int = 3600
    ) -> str:
        """获取预签名 URL"""
        from datetime import timedelta

        return self._client.presigned_get_object(
            bucket,
            name,
            expires=timedelta(seconds=expires)
        )

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        recursive: bool = True
    ) -> list[str]:
        """列出对象"""
        objects = self._client.list_objects(
            bucket,
            prefix=prefix,
            recursive=recursive
        )
        return [obj.object_name for obj in objects]

    async def bucket_exists(self, bucket: str) -> bool:
        """检查存储桶是否存在"""
        return self._client.bucket_exists(bucket)

    async def create_bucket(self, bucket: str) -> bool:
        """创建存储桶"""
        try:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
            return True
        except S3Error:
            return False
