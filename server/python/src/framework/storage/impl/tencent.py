"""
腾讯云 COS 存储实现
"""

from qcloud_cos import CosConfig, CosS3Client
from typing import Any

from framework.config.settings import TencentCosSettings


class TencentStorage:
    """腾讯云 COS 存储实现"""

    def __init__(self, config: TencentCosSettings):
        self._config = config

        cos_config = CosConfig(
            Region=config.region,
            SecretId=config.secret_id,
            SecretKey=config.secret_key,
            Token=config.token,
            Scheme=config.scheme
        )
        self._client = CosS3Client(cos_config)

    async def upload(
        self,
        bucket: str,
        name: str,
        data: bytes,
        content_type: str | None = None
    ) -> str:
        """上传文件"""
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type

        self._client.put_object(
            Bucket=bucket,
            Body=data,
            Key=name,
            **headers
        )
        return f"{bucket}/{name}"

    async def download(self, bucket: str, name: str) -> bytes:
        """下载文件"""
        response = self._client.get_object(Bucket=bucket, Key=name)
        return response["Body"].read()

    async def delete(self, bucket: str, name: str) -> bool:
        """删除文件"""
        try:
            self._client.delete_object(Bucket=bucket, Key=name)
            return True
        except Exception:
            return False

    async def exists(self, bucket: str, name: str) -> bool:
        """检查文件是否存在"""
        try:
            self._client.head_object(Bucket=bucket, Key=name)
            return True
        except Exception:
            return False

    async def get_presigned_url(
        self,
        bucket: str,
        name: str,
        expires: int = 3600
    ) -> str:
        """获取预签名 URL"""
        return self._client.get_presigned_download_url(
            Bucket=bucket,
            Key=name,
            Expired=expires
        )

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        recursive: bool = True
    ) -> list[str]:
        """列出对象"""
        response = self._client.list_objects(Bucket=bucket, Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]

    async def bucket_exists(self, bucket: str) -> bool:
        """检查存储桶是否存在"""
        try:
            self._client.head_bucket(Bucket=bucket)
            return True
        except Exception:
            return False

    async def create_bucket(self, bucket: str) -> bool:
        """创建存储桶"""
        try:
            self._client.create_bucket(Bucket=bucket)
            return True
        except Exception:
            return False
