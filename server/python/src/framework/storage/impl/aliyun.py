"""
阿里云 OSS 存储实现
"""

import oss2
from typing import Any

from framework.config.settings import AliyunOssSettings


class AliyunStorage:
    """阿里云 OSS 存储实现"""

    def __init__(self, config: AliyunOssSettings):
        self._config = config
        self._auth = oss2.Auth(config.access_key_id, config.access_key_secret)
        self._bucket = oss2.Bucket(
            self._auth,
            config.endpoint,
            config.endpoint.split("//")[1].split(".")[0] if "//" in config.endpoint else ""
        )

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

        self._bucket.put_object(name, data, headers=headers)
        return f"{bucket}/{name}"

    async def download(self, bucket: str, name: str) -> bytes:
        """下载文件"""
        result = self._bucket.get_object(name)
        return result.read()

    async def delete(self, bucket: str, name: str) -> bool:
        """删除文件"""
        try:
            self._bucket.delete_object(name)
            return True
        except Exception:
            return False

    async def exists(self, bucket: str, name: str) -> bool:
        """检查文件是否存在"""
        return self._bucket.object_exists(name)

    async def get_presigned_url(
        self,
        bucket: str,
        name: str,
        expires: int = 3600
    ) -> str:
        """获取预签名 URL"""
        return self._bucket.sign_url("GET", name, expires)

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        recursive: bool = True
    ) -> list[str]:
        """列出对象"""
        objects = oss2.ObjectIterator(self._bucket, prefix=prefix)
        return [obj.key for obj in objects]

    async def bucket_exists(self, bucket: str) -> bool:
        """检查存储桶是否存在"""
        try:
            self._bucket.get_bucket_info()
            return True
        except Exception:
            return False

    async def create_bucket(self, bucket: str) -> bool:
        """创建存储桶"""
        # 阿里云 OSS 不支持在 API 中创建 Bucket
        return False
