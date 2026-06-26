"""
插件存储服务

提供插件包的 MinIO 存储功能。
存储路径：plugins/{plugin_id}/{version}.zip
"""

from pathlib import Path

from loguru import logger

from framework.configs import get_settings
from framework.storage import get_storage_provider


class PluginStorageService:
    """插件存储服务"""

    def __init__(self):
        """初始化存储服务"""
        settings = get_settings()
        self._storage = get_storage_provider(settings.oss)
        self._bucket_name = settings.plugin.storage_bucket
        self._initialized = False

    async def _ensure_bucket(self) -> None:
        """确保存储桶存在"""
        if self._initialized:
            return

        try:
            exists = await self._storage.bucket_exists(self._bucket_name)
            if not exists:
                await self._storage.create_bucket(self._bucket_name)
                logger.info(f"创建插件存储桶: {self._bucket_name}")
            self._initialized = True
        except Exception as e:
            logger.error(f"初始化插件存储桶失败: {e}")
            raise

    async def upload_plugin_package(
        self,
        plugin_id: str,
        version: str,
        package_data: bytes,
    ) -> str:
        """
        上传插件包到 MinIO

        Args:
            plugin_id: 插件ID，格式：author/name
            version: 版本号
            package_data: 插件包二进制数据

        Returns:
            str: 存储路径（object key）

        Raises:
            Exception: 上传失败
        """
        await self._ensure_bucket()

        # 构建存储路径：{plugin_id}/{version}.zip
        # 将 plugin_id 中的 "/" 替换为 "/" 保持原样（MinIO 支持路径分隔符）
        object_key = f"{plugin_id}/{version}.zip"

        try:
            await self._storage.upload(
                bucket=self._bucket_name,
                name=object_key,
                data=package_data,
                content_type="application/zip",
            )
            logger.info(f"上传插件包成功: {self._bucket_name}/{object_key}")
            return object_key
        except Exception as e:
            logger.error(f"上传插件包失败: {plugin_id}/{version} - {e}")
            raise

    async def delete_plugin_package(self, plugin_id: str, version: str) -> bool:
        """
        删除插件包

        Args:
            plugin_id: 插件ID
            version: 版本号

        Returns:
            bool: 是否删除成功
        """
        object_key = f"{plugin_id}/{version}.zip"

        try:
            result = await self._storage.delete(self._bucket_name, object_key)
            if result:
                logger.info(f"删除插件包成功: {self._bucket_name}/{object_key}")
            return result
        except Exception as e:
            logger.error(f"删除插件包失败: {plugin_id}/{version} - {e}")
            return False

    async def delete_all_versions(self, plugin_id: str) -> int:
        """
        删除插件的所有版本

        Args:
            plugin_id: 插件ID

        Returns:
            int: 删除的文件数量
        """
        try:
            # 列出该插件的所有版本
            objects = await self._storage.list_objects(
                bucket=self._bucket_name,
                prefix=f"{plugin_id}/",
                recursive=True,
            )

            deleted_count = 0
            for object_key in objects:
                if await self._storage.delete(self._bucket_name, object_key):
                    deleted_count += 1

            logger.info(f"删除插件所有版本: {plugin_id}, 共 {deleted_count} 个文件")
            return deleted_count
        except Exception as e:
            logger.error(f"删除插件所有版本失败: {plugin_id} - {e}")
            return 0

    async def get_download_url(
        self,
        plugin_id: str,
        version: str,
        expires: int = 3600,
    ) -> str:
        """
        获取插件包下载链接（预签名 URL）

        Args:
            plugin_id: 插件ID
            version: 版本号
            expires: 链接有效期（秒），默认 1 小时

        Returns:
            str: 预签名下载 URL
        """
        object_key = f"{plugin_id}/{version}.zip"
        return await self._storage.get_presigned_url(
            bucket=self._bucket_name,
            name=object_key,
            expires=expires,
        )

    async def package_exists(self, plugin_id: str, version: str) -> bool:
        """
        检查插件包是否存在

        Args:
            plugin_id: 插件ID
            version: 版本号

        Returns:
            bool: 是否存在
        """
        object_key = f"{plugin_id}/{version}.zip"
        return await self._storage.exists(self._bucket_name, object_key)

    async def download_package(self, plugin_id: str, version: str) -> bytes:
        """
        下载插件包

        Args:
            plugin_id: 插件ID
            version: 版本号

        Returns:
            bytes: 插件包二进制数据
        """
        object_key = f"{plugin_id}/{version}.zip"
        return await self._storage.download(self._bucket_name, object_key)


# 单例实例
plugin_storage_service = PluginStorageService()
