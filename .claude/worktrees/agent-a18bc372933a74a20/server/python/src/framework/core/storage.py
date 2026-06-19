"""
存储接口定义

使用 Python Protocol 定义统一的存储接口。
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageProvider(Protocol):
    """
    存储提供者协议

    定义统一的对象存储接口，支持 MinIO、阿里云 OSS、腾讯云 COS 等实现。
    """

    async def upload(
        self,
        bucket: str,
        name: str,
        data: bytes,
        content_type: str | None = None
    ) -> str:
        """
        上传文件

        Args:
            bucket: 存储桶名称
            name: 对象名称（路径）
            data: 文件数据
            content_type: 内容类型

        Returns:
            str: 对象访问路径
        """
        ...

    async def download(self, bucket: str, name: str) -> bytes:
        """
        下载文件

        Args:
            bucket: 存储桶名称
            name: 对象名称

        Returns:
            bytes: 文件数据
        """
        ...

    async def delete(self, bucket: str, name: str) -> bool:
        """
        删除文件

        Args:
            bucket: 存储桶名称
            name: 对象名称

        Returns:
            bool: 是否成功
        """
        ...

    async def exists(self, bucket: str, name: str) -> bool:
        """
        检查文件是否存在

        Args:
            bucket: 存储桶名称
            name: 对象名称

        Returns:
            bool: 是否存在
        """
        ...

    async def get_presigned_url(
        self,
        bucket: str,
        name: str,
        expires: int = 3600
    ) -> str:
        """
        获取预签名 URL

        Args:
            bucket: 存储桶名称
            name: 对象名称
            expires: 过期时间（秒）

        Returns:
            str: 预签名 URL
        """
        ...

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        recursive: bool = True
    ) -> list[str]:
        """
        列出对象

        Args:
            bucket: 存储桶名称
            prefix: 前缀
            recursive: 是否递归

        Returns:
            list[str]: 对象名称列表
        """
        ...

    async def bucket_exists(self, bucket: str) -> bool:
        """
        检查存储桶是否存在

        Args:
            bucket: 存储桶名称

        Returns:
            bool: 是否存在
        """
        ...

    async def create_bucket(self, bucket: str) -> bool:
        """
        创建存储桶

        Args:
            bucket: 存储桶名称

        Returns:
            bool: 是否成功
        """
        ...
