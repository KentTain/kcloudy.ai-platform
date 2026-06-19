"""
租户存储管理器

根据租户配置路由到独立存储桶/服务，支持：
- 独立存储服务物理隔离（不同 endpoint）
- 独立 Bucket 逻辑隔离
- 默认 Bucket + 路径前缀逻辑隔离
- 存储桶自动创建
- 存储客户端缓存
"""

from datetime import datetime, timedelta
from typing import Any

from loguru import logger

from framework.storage.impl.minio import MinioStorage
from framework.tenant.context import get_tenant_id
from framework.tenant.protocols import TenantStorageConfig
from framework.database.mixins.tenant import should_skip_tenant

_logger = logger.bind(name=__name__)

# 最大实例客户端数
MAX_INSTANCE_STORAGES = 50
# 实例空闲超时（秒）
INSTANCE_IDLE_TIMEOUT = 600


class TenantStorageManager:
    """
    租户存储管理器

    管理：
    - 默认存储实例
    - 租户级存储桶路由
    - 租户级存储服务实例（物理隔离）
    """

    def __init__(self, default_storage: MinioStorage, default_bucket: str):
        """
        初始化存储管理器

        Args:
            default_storage: 默认存储实例
            default_bucket: 默认存储桶名称
        """
        self._default_storage = default_storage
        self._default_bucket = default_bucket
        self._bucket_map: dict[str, str] = {}  # tenant_id -> bucket_name

        # 物理隔离实例客户端
        self._instance_storages: dict[str, MinioStorage] = {}  # endpoint -> storage
        self._instance_access_times: dict[str, datetime] = {}

    @staticmethod
    def _is_physical_isolation(config: TenantStorageConfig | None) -> bool:
        """判断是否使用物理隔离"""
        return bool(config and config.endpoint)

    def register_bucket(self, tenant_id: str, bucket: str) -> None:
        """
        注册租户存储桶

        Args:
            tenant_id: 租户 ID
            bucket: 存储桶名称
        """
        self._bucket_map[tenant_id] = bucket
        _logger.debug(f"注册租户存储桶: {tenant_id} -> {bucket}")

    def unregister_bucket(self, tenant_id: str) -> None:
        """
        注销租户存储桶

        Args:
            tenant_id: 租户 ID
        """
        self._bucket_map.pop(tenant_id, None)

    def get_bucket(
        self,
        tenant_id: str | None = None,
        config: TenantStorageConfig | None = None,
    ) -> str:
        """
        获取租户存储桶名称

        Args:
            tenant_id: 租户 ID
            config: 租户存储配置

        Returns:
            str: 存储桶名称
        """
        if config and config.bucket:
            return config.bucket

        if tenant_id and tenant_id in self._bucket_map:
            return self._bucket_map[tenant_id]

        return self._default_bucket

    def get_storage(
        self,
        config: TenantStorageConfig | None = None,
    ) -> MinioStorage:
        """
        获取存储服务客户端

        Args:
            config: 租户存储配置

        Returns:
            MinioStorage: 存储客户端
        """
        if not self._is_physical_isolation(config):
            return self._default_storage

        assert config is not None
        instance_key = config.endpoint

        if instance_key in self._instance_storages:
            self._instance_access_times[instance_key] = datetime.now()
            return self._instance_storages[instance_key]

        storage = self._create_storage(config)
        self._instance_storages[instance_key] = storage
        self._instance_access_times[instance_key] = datetime.now()
        _logger.debug(f"创建实例存储客户端: {instance_key}")
        return storage

    def _create_storage(self, config: TenantStorageConfig) -> MinioStorage:
        """
        创建存储服务客户端

        Args:
            config: 租户存储配置

        Returns:
            MinioStorage: 存储客户端
        """
        from framework.configs.settings import MinioSettings

        settings = MinioSettings(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.endpoint.startswith("https"),
        )
        return MinioStorage(settings)

    def _build_path(
        self,
        path: str,
        tenant_id: str | None = None,
        config: TenantStorageConfig | None = None,
        skip_tenant: bool = False,
    ) -> str:
        """
        构建对象路径

        Args:
            path: 原始路径
            tenant_id: 租户 ID
            config: 租户存储配置
            skip_tenant: 是否跳过租户前缀

        Returns:
            str: 实际存储路径
        """
        if skip_tenant or should_skip_tenant():
            return path

        # 有物理隔离或独立存储桶，不添加前缀
        if self._is_physical_isolation(config):
            return path.lstrip("/")

        if config and config.bucket:
            return path.lstrip("/")

        if tenant_id and tenant_id in self._bucket_map:
            return path.lstrip("/")

        # 使用默认存储桶，添加租户前缀
        actual_tenant_id = tenant_id or get_tenant_id()
        if actual_tenant_id:
            return f"{actual_tenant_id}/{path.lstrip('/')}"

        return path.lstrip("/")

    async def upload(
        self,
        path: str,
        data: bytes,
        tenant_id: str | None = None,
        config: TenantStorageConfig | None = None,
        content_type: str | None = None,
        skip_tenant: bool = False,
    ) -> str:
        """上传文件"""
        storage = self.get_storage(config)
        bucket = self.get_bucket(tenant_id, config)
        actual_path = self._build_path(path, tenant_id, config, skip_tenant)
        await self._ensure_bucket_exists(storage, bucket)
        return await storage.upload(bucket, actual_path, data, content_type)

    async def download(
        self,
        path: str,
        tenant_id: str | None = None,
        config: TenantStorageConfig | None = None,
        skip_tenant: bool = False,
    ) -> bytes:
        """下载文件"""
        storage = self.get_storage(config)
        bucket = self.get_bucket(tenant_id, config)
        actual_path = self._build_path(path, tenant_id, config, skip_tenant)
        return await storage.download(bucket, actual_path)

    async def delete(
        self,
        path: str,
        tenant_id: str | None = None,
        config: TenantStorageConfig | None = None,
        skip_tenant: bool = False,
    ) -> bool:
        """删除文件"""
        storage = self.get_storage(config)
        bucket = self.get_bucket(tenant_id, config)
        actual_path = self._build_path(path, tenant_id, config, skip_tenant)
        return await storage.delete(bucket, actual_path)

    async def exists(
        self,
        path: str,
        tenant_id: str | None = None,
        config: TenantStorageConfig | None = None,
        skip_tenant: bool = False,
    ) -> bool:
        """检查文件是否存在"""
        storage = self.get_storage(config)
        bucket = self.get_bucket(tenant_id, config)
        actual_path = self._build_path(path, tenant_id, config, skip_tenant)
        return await storage.exists(bucket, actual_path)

    async def get_presigned_url(
        self,
        path: str,
        tenant_id: str | None = None,
        config: TenantStorageConfig | None = None,
        expires: int = 3600,
        skip_tenant: bool = False,
    ) -> str:
        """获取预签名 URL"""
        storage = self.get_storage(config)
        bucket = self.get_bucket(tenant_id, config)
        actual_path = self._build_path(path, tenant_id, config, skip_tenant)
        return await storage.get_presigned_url(bucket, actual_path, expires)

    async def list_objects(
        self,
        prefix: str = "",
        tenant_id: str | None = None,
        config: TenantStorageConfig | None = None,
        recursive: bool = True,
        skip_tenant: bool = False,
    ) -> list[str]:
        """列出对象"""
        storage = self.get_storage(config)
        bucket = self.get_bucket(tenant_id, config)
        actual_prefix = self._build_path(prefix, tenant_id, config, skip_tenant)

        objects = await storage.list_objects(bucket, actual_prefix, recursive)

        # 如果使用租户前缀，移除前缀返回原始路径
        if (
            not skip_tenant
            and not should_skip_tenant()
            and not self._is_physical_isolation(config)
        ):
            actual_tenant_id = tenant_id or get_tenant_id()
            if actual_tenant_id and (not config or not config.bucket):
                tenant_prefix = f"{actual_tenant_id}/"
                return [
                    obj[len(tenant_prefix):] if obj.startswith(tenant_prefix) else obj
                    for obj in objects
                ]

        return objects

    async def _ensure_bucket_exists(self, storage: MinioStorage, bucket: str) -> None:
        """
        确保存储桶存在

        Args:
            storage: 存储客户端
            bucket: 存储桶名称
        """
        try:
            if not await storage.bucket_exists(bucket):
                await storage.create_bucket(bucket)
                _logger.info(f"创建存储桶: {bucket}")
        except Exception as e:
            _logger.warning(f"检查/创建存储桶失败: {bucket}, error={e}")

    async def release_idle_instances(self, timeout: int | None = None) -> int:
        """
        释放空闲实例客户端

        Args:
            timeout: 空闲超时（秒）

        Returns:
            int: 释放的客户端数量
        """
        if timeout is None:
            timeout = INSTANCE_IDLE_TIMEOUT

        now = datetime.now()
        threshold = now - timedelta(seconds=timeout)

        released = 0
        to_release: list[str] = []

        for key, last_access in self._instance_access_times.items():
            if last_access < threshold:
                to_release.append(key)

        for key in to_release:
            self._instance_storages.pop(key, None)
            self._instance_access_times.pop(key, None)
            released += 1
            _logger.debug(f"释放空闲存储客户端: {key}")

        return released

    async def close(self) -> None:
        """关闭所有客户端"""
        for key in list(self._instance_storages.keys()):
            self._instance_storages.pop(key, None)
            self._instance_access_times.pop(key, None)
        _logger.info("所有租户存储客户端已关闭")


# 全局存储管理器实例
_storage_manager: TenantStorageManager | None = None


def get_storage_manager() -> TenantStorageManager:
    """
    获取全局存储管理器实例

    Returns:
        TenantStorageManager: 存储管理器实例
    """
    global _storage_manager
    if _storage_manager is None:
        raise RuntimeError("TenantStorageManager 未初始化")
    return _storage_manager


def init_storage_manager(default_storage: MinioStorage, default_bucket: str) -> TenantStorageManager:
    """
    初始化存储管理器

    Args:
        default_storage: 默认存储实例
        default_bucket: 默认存储桶名称

    Returns:
        TenantStorageManager: 存储管理器实例
    """
    global _storage_manager
    _storage_manager = TenantStorageManager(default_storage, default_bucket)
    return _storage_manager
