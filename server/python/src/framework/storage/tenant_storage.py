"""
租户感知的存储服务

自动为存储路径添加租户目录前缀。
"""

from typing import Any

from framework.storage.impl.minio import MinioStorage
from framework.tenant.context import get_tenant_id
from framework.database.mixins.tenant import should_skip_tenant


def _build_object_path(path: str, skip_tenant: bool = False) -> str:
    """
    构建带租户前缀的对象路径

    Args:
        path: 原始路径
        skip_tenant: 是否跳过租户前缀

    Returns:
        带租户前缀的路径
    """
    if skip_tenant or should_skip_tenant():
        return path

    tenant_id = get_tenant_id()
    if tenant_id:
        # 移除开头的斜杠
        path = path.lstrip("/")
        return f"{tenant_id}/{path}"
    return path


class TenantMinioStorage:
    """
    租户感知的 MinIO 存储服务

    自动为所有对象路径添加租户目录前缀。

    使用示例：
        # 上传文件（自动添加租户前缀）
        await TenantMinioStorage.upload("bucket", "avatars/user_123.jpg", data)
        # 实际路径: "tenant_001/avatars/user_123.jpg"

        # 跳过租户前缀（管理员场景）
        await TenantMinioStorage.upload("bucket", "system/logo.png", data, skip_tenant=True)
        # 实际路径: "system/logo.png"
    """

    _storage: MinioStorage | None = None

    @classmethod
    def init(cls, storage: MinioStorage) -> None:
        """初始化存储服务"""
        cls._storage = storage

    @classmethod
    def _get_storage(cls) -> MinioStorage:
        """获取存储服务实例"""
        if cls._storage is None:
            raise RuntimeError("TenantMinioStorage 未初始化，请先调用 init()")
        return cls._storage

    @classmethod
    async def upload(
        cls,
        bucket: str,
        name: str,
        data: bytes,
        content_type: str | None = None,
        skip_tenant: bool = False
    ) -> str:
        """
        上传文件，自动添加租户前缀

        场景：上传文件自动添加前缀
        WHEN 调用 StorageService.upload("avatars/user_123.jpg", file)
        THEN 实际存储路径为 `tenant_001/avatars/user_123.jpg`

        场景：管理员场景跳过前缀
        WHEN 调用 StorageService.upload("system/logo.png", file, skip_tenant=True)
        THEN 实际存储路径为 `system/logo.png`

        Args:
            bucket: 存储桶名称
            name: 对象名称/路径
            data: 文件数据
            content_type: 内容类型
            skip_tenant: 是否跳过租户前缀

        Returns:
            str: 对象完整路径
        """
        storage = cls._get_storage()
        actual_path = _build_object_path(name, skip_tenant)
        return await storage.upload(bucket, actual_path, data, content_type)

    @classmethod
    async def download(
        cls,
        bucket: str,
        name: str,
        skip_tenant: bool = False
    ) -> bytes:
        """
        下载文件，自动添加租户前缀

        场景：下载文件自动添加前缀
        WHEN 调用 StorageService.download("avatars/user_123.jpg")
        THEN 实际下载路径为 `tenant_001/avatars/user_123.jpg`

        Args:
            bucket: 存储桶名称
            name: 对象名称/路径
            skip_tenant: 是否跳过租户前缀

        Returns:
            bytes: 文件数据
        """
        storage = cls._get_storage()
        actual_path = _build_object_path(name, skip_tenant)
        return await storage.download(bucket, actual_path)

    @classmethod
    async def delete(
        cls,
        bucket: str,
        name: str,
        skip_tenant: bool = False
    ) -> bool:
        """
        删除文件，自动添加租户前缀

        场景：删除文件自动添加前缀
        WHEN 调用 StorageService.delete("avatars/user_123.jpg")
        THEN 实际删除路径为 `tenant_001/avatars/user_123.jpg`

        Args:
            bucket: 存储桶名称
            name: 对象名称/路径
            skip_tenant: 是否跳过租户前缀

        Returns:
            bool: 是否删除成功
        """
        storage = cls._get_storage()
        actual_path = _build_object_path(name, skip_tenant)
        return await storage.delete(bucket, actual_path)

    @classmethod
    async def exists(
        cls,
        bucket: str,
        name: str,
        skip_tenant: bool = False
    ) -> bool:
        """
        检查文件是否存在，自动添加租户前缀

        Args:
            bucket: 存储桶名称
            name: 对象名称/路径
            skip_tenant: 是否跳过租户前缀

        Returns:
            bool: 文件是否存在
        """
        storage = cls._get_storage()
        actual_path = _build_object_path(name, skip_tenant)
        return await storage.exists(bucket, actual_path)

    @classmethod
    async def get_presigned_url(
        cls,
        bucket: str,
        name: str,
        expires: int = 3600,
        skip_tenant: bool = False
    ) -> str:
        """
        获取预签名 URL，自动添加租户前缀

        场景：生成预签名 URL
        WHEN 调用 StorageService.get_presigned_url("documents/report.pdf")
        THEN 返回的 URL 指向 `tenant_001/documents/report.pdf`

        Args:
            bucket: 存储桶名称
            name: 对象名称/路径
            expires: URL 过期时间（秒）
            skip_tenant: 是否跳过租户前缀

        Returns:
            str: 预签名 URL
        """
        storage = cls._get_storage()
        actual_path = _build_object_path(name, skip_tenant)
        return await storage.get_presigned_url(bucket, actual_path, expires)

    @classmethod
    async def list_objects(
        cls,
        bucket: str,
        prefix: str = "",
        recursive: bool = True,
        skip_tenant: bool = False
    ) -> list[str]:
        """
        列出对象，自动添加租户前缀过滤

        场景：列举对象自动过滤
        WHEN 调用 StorageService.list_objects("documents/")
        THEN 只返回 `tenant_001/documents/` 下的对象

        Args:
            bucket: 存储桶名称
            prefix: 对象前缀
            recursive: 是否递归列出
            skip_tenant: 是否跳过租户前缀

        Returns:
            list[str]: 对象名称列表（已移除租户前缀）
        """
        storage = cls._get_storage()
        actual_prefix = _build_object_path(prefix, skip_tenant)
        objects = await storage.list_objects(bucket, actual_prefix, recursive)

        if skip_tenant or should_skip_tenant():
            return objects

        # 移除租户前缀，只返回原始路径
        tenant_id = get_tenant_id()
        if tenant_id:
            tenant_prefix = f"{tenant_id}/"
            return [
                obj[len(tenant_prefix):] if obj.startswith(tenant_prefix) else obj
                for obj in objects
            ]
        return objects

    @classmethod
    async def bucket_exists(cls, bucket: str) -> bool:
        """检查存储桶是否存在"""
        storage = cls._get_storage()
        return await storage.bucket_exists(bucket)

    @classmethod
    async def create_bucket(cls, bucket: str) -> bool:
        """创建存储桶"""
        storage = cls._get_storage()
        return await storage.create_bucket(bucket)


# 便捷函数
async def tenant_storage_upload(
    bucket: str, name: str, data: bytes,
    content_type: str | None = None, skip_tenant: bool = False
) -> str:
    """上传租户文件"""
    return await TenantMinioStorage.upload(bucket, name, data, content_type, skip_tenant)


async def tenant_storage_download(bucket: str, name: str, skip_tenant: bool = False) -> bytes:
    """下载租户文件"""
    return await TenantMinioStorage.download(bucket, name, skip_tenant)


async def tenant_storage_delete(bucket: str, name: str, skip_tenant: bool = False) -> bool:
    """删除租户文件"""
    return await TenantMinioStorage.delete(bucket, name, skip_tenant)
