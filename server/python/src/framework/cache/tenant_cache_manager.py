"""
租户缓存管理器

根据租户配置路由到独立 Redis DB，支持：
- 独立 Redis DB 物理隔离
- 默认 Redis DB + Key 前缀逻辑隔离
- Redis 客户端缓存
"""

from typing import Any, Optional

from redis.asyncio import Redis, ConnectionPool
from loguru import logger

from framework.cache.redis_util import RedisUtil
from framework.tenant.context import get_tenant_id
from framework.tenant.protocols import TenantCacheConfig
from framework.database.mixins.tenant import should_skip_tenant

_logger = logger.bind(name=__name__)

# Redis DB 编号范围
MIN_DB = 0
MAX_DB = 15

# Key 前缀格式
TENANT_KEY_PREFIX = "{tenant_id}:{key}"
TENANT_QUEUE_PREFIX = "{tenant_id}:queue:{queue_name}"
TENANT_CHANNEL_PREFIX = "{tenant_id}:channel:{channel_name}"
TENANT_LOCK_PREFIX = "{tenant_id}:lock:{lock_key}"


class TenantCacheManager:
    """
    租户缓存管理器

    管理：
    - 默认 Redis 客户端
    - 租户级 Redis DB 客户端
    - DB 编号分配
    """

    def __init__(self, default_client: Redis):
        """
        初始化缓存管理器

        Args:
            default_client: 默认 Redis 客户端
        """
        self._default_client = default_client
        self._db_clients: dict[int, Redis] = {}  # db_index -> client
        self._tenant_db_map: dict[str, int] = {}  # tenant_id -> db_index
        self._db_usage: dict[int, set[str]] = {}  # db_index -> tenant_ids

    def register_tenant_db(self, tenant_id: str, db: int) -> None:
        """
        注册租户 Redis DB

        Args:
            tenant_id: 租户 ID
            db: Redis DB 编号

        Raises:
            ValueError: DB 编号超出范围
        """
        if db < MIN_DB or db > MAX_DB:
            raise ValueError(f"Redis DB 编号必须在 {MIN_DB}-{MAX_DB} 范围内")

        self._tenant_db_map[tenant_id] = db
        if db not in self._db_usage:
            self._db_usage[db] = set()
        self._db_usage[db].add(tenant_id)

        _logger.debug(f"注册租户 Redis DB: {tenant_id} -> DB {db}")

    def unregister_tenant(self, tenant_id: str) -> None:
        """
        注销租户

        Args:
            tenant_id: 租户 ID
        """
        db = self._tenant_db_map.pop(tenant_id, None)
        if db is not None and db in self._db_usage:
            self._db_usage[db].discard(tenant_id)

    def get_db(
        self,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
    ) -> int:
        """
        获取租户 Redis DB 编号

        Args:
            tenant_id: 租户 ID
            config: 租户缓存配置

        Returns:
            int: Redis DB 编号
        """
        # 有配置且配置了 db，使用配置的 DB
        if config and config.db is not None:
            return config.db

        # 从注册表查找
        if tenant_id and tenant_id in self._tenant_db_map:
            return self._tenant_db_map[tenant_id]

        # 使用默认 DB
        return 0

    async def get_client(
        self,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
    ) -> Redis:
        """
        获取租户 Redis 客户端

        Args:
            tenant_id: 租户 ID
            config: 租户缓存配置

        Returns:
            Redis: Redis 客户端
        """
        db = self.get_db(tenant_id, config)

        # DB 0 使用默认客户端
        if db == 0:
            return self._default_client

        # 检查缓存
        if db in self._db_clients:
            return self._db_clients[db]

        # 创建新的客户端
        client = await self._create_db_client(db)
        self._db_clients[db] = client
        return client

    async def _create_db_client(self, db: int) -> Redis:
        """
        创建指定 DB 的 Redis 客户端

        Args:
            db: Redis DB 编号

        Returns:
            Redis: Redis 客户端
        """
        # 从默认客户端获取连接信息
        default_pool = self._default_client.connection_pool
        connection_kwargs = default_pool.connection_kwargs.copy()
        connection_kwargs["db"] = db

        pool = ConnectionPool(**connection_kwargs)
        client = Redis(connection_pool=pool)

        _logger.debug(f"创建 Redis DB {db} 客户端")
        return client

    def _build_key(
        self,
        key: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        skip_tenant: bool = False,
    ) -> str:
        """
        构建带租户前缀的 Key

        Args:
            key: 原始 Key
            tenant_id: 租户 ID
            config: 租户缓存配置
            skip_tenant: 是否跳过租户前缀

        Returns:
            str: 实际 Key
        """
        if skip_tenant or should_skip_tenant():
            return key

        # 有独立 Redis DB 配置，不添加前缀
        if config and config.db is not None:
            return key

        # 从注册表找到独立 DB，不添加前缀
        if tenant_id and tenant_id in self._tenant_db_map:
            return key

        # 使用默认 Redis DB，添加租户前缀
        actual_tenant_id = tenant_id or get_tenant_id()
        if actual_tenant_id:
            return TENANT_KEY_PREFIX.format(tenant_id=actual_tenant_id, key=key)

        return key

    def _build_stream_key(
        self,
        queue_name: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        skip_tenant: bool = False,
    ) -> str:
        """
        构建带租户前缀的 Stream Key

        Args:
            queue_name: 队列名称
            tenant_id: 租户 ID
            config: 租户缓存配置
            skip_tenant: 是否跳过租户前缀

        Returns:
            str: 实际 Stream Key
        """
        if skip_tenant or should_skip_tenant():
            return f"queue:{queue_name}"

        if config and config.db is not None:
            return f"queue:{queue_name}"

        if tenant_id and tenant_id in self._tenant_db_map:
            return f"queue:{queue_name}"

        actual_tenant_id = tenant_id or get_tenant_id()
        if actual_tenant_id:
            return TENANT_QUEUE_PREFIX.format(tenant_id=actual_tenant_id, queue_name=queue_name)

        return f"queue:{queue_name}"

    # =========================================================================
    # 字符串操作
    # =========================================================================

    async def set(
        self,
        key: str,
        value: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        ttl: int | None = None,
        nx: bool = False,
        skip_tenant: bool = False,
    ) -> bool:
        """设置键值对"""
        client = await self.get_client(tenant_id, config)
        actual_key = self._build_key(key, tenant_id, config, skip_tenant)
        return await client.set(actual_key, value, ex=ttl, nx=nx)

    async def get(
        self,
        key: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        skip_tenant: bool = False,
    ) -> str | None:
        """获取键值"""
        client = await self.get_client(tenant_id, config)
        actual_key = self._build_key(key, tenant_id, config, skip_tenant)
        result = await client.get(actual_key)
        if result is None:
            return None
        return result.decode() if isinstance(result, bytes) else result

    async def delete(
        self,
        key: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        skip_tenant: bool = False,
    ) -> int:
        """删除键"""
        client = await self.get_client(tenant_id, config)
        actual_key = self._build_key(key, tenant_id, config, skip_tenant)
        return await client.delete(actual_key)

    async def exists(
        self,
        key: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        skip_tenant: bool = False,
    ) -> bool:
        """检查键是否存在"""
        client = await self.get_client(tenant_id, config)
        actual_key = self._build_key(key, tenant_id, config, skip_tenant)
        return await client.exists(actual_key) > 0

    # =========================================================================
    # Stream 操作（队列）
    # =========================================================================

    async def xadd(
        self,
        queue_name: str,
        fields: dict[str, Any],
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        id: str = "*",
        skip_tenant: bool = False,
    ) -> str:
        """添加 Stream 消息"""
        client = await self.get_client(tenant_id, config)
        actual_stream = self._build_stream_key(queue_name, tenant_id, config, skip_tenant)
        result = await client.xadd(actual_stream, fields, id=id)
        return result.decode() if isinstance(result, bytes) else result

    async def xreadgroup(
        self,
        groupname: str,
        consumername: str,
        queue_name: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        count: int = 1,
        block: int | None = None,
        skip_tenant: bool = False,
    ) -> list:
        """使用消费者组读取 Stream 消息"""
        client = await self.get_client(tenant_id, config)
        actual_stream = self._build_stream_key(queue_name, tenant_id, config, skip_tenant)
        return await client.xreadgroup(
            groupname=groupname,
            consumername=consumername,
            streams={actual_stream: ">"},
            count=count,
            block=block
        )

    async def xack(
        self,
        queue_name: str,
        group: str,
        *ids: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        skip_tenant: bool = False,
    ) -> int:
        """确认 Stream 消息"""
        client = await self.get_client(tenant_id, config)
        actual_stream = self._build_stream_key(queue_name, tenant_id, config, skip_tenant)
        return await client.xack(actual_stream, group, *ids)

    # =========================================================================
    # 发布订阅
    # =========================================================================

    async def publish(
        self,
        channel: str,
        message: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        skip_tenant: bool = False,
    ) -> int:
        """发布消息"""
        client = await self.get_client(tenant_id, config)
        actual_channel = channel
        if not skip_tenant and not should_skip_tenant():
            if not (config and config.db is not None):
                actual_tenant_id = tenant_id or get_tenant_id()
                if actual_tenant_id and actual_tenant_id not in self._tenant_db_map:
                    actual_channel = TENANT_CHANNEL_PREFIX.format(
                        tenant_id=actual_tenant_id,
                        channel_name=channel
                    )
        return await client.publish(actual_channel, message)

    # =========================================================================
    # 分布式锁
    # =========================================================================

    async def acquire_lock(
        self,
        lock_key: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        ttl: int = 30,
        skip_tenant: bool = False,
    ) -> bool:
        """获取分布式锁"""
        client = await self.get_client(tenant_id, config)
        actual_key = lock_key
        if not skip_tenant and not should_skip_tenant():
            if not (config and config.db is not None):
                actual_tenant_id = tenant_id or get_tenant_id()
                if actual_tenant_id and actual_tenant_id not in self._tenant_db_map:
                    actual_key = TENANT_LOCK_PREFIX.format(
                        tenant_id=actual_tenant_id,
                        lock_key=lock_key
                    )
        return await client.set(actual_key, "1", ex=ttl, nx=True)

    async def release_lock(
        self,
        lock_key: str,
        tenant_id: str | None = None,
        config: TenantCacheConfig | None = None,
        skip_tenant: bool = False,
    ) -> bool:
        """释放分布式锁"""
        client = await self.get_client(tenant_id, config)
        actual_key = lock_key
        if not skip_tenant and not should_skip_tenant():
            if not (config and config.db is not None):
                actual_tenant_id = tenant_id or get_tenant_id()
                if actual_tenant_id and actual_tenant_id not in self._tenant_db_map:
                    actual_key = TENANT_LOCK_PREFIX.format(
                        tenant_id=actual_tenant_id,
                        lock_key=lock_key
                    )
        result = await client.delete(actual_key)
        return result > 0

    # =========================================================================
    # 管理
    # =========================================================================

    async def close(self) -> None:
        """关闭所有客户端"""
        for db, client in self._db_clients.items():
            try:
                await client.aclose()
            except Exception as e:
                _logger.warning(f"关闭 Redis DB {db} 客户端失败: {e}")

        self._db_clients.clear()
        _logger.info("所有租户 Redis 客户端已关闭")

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_db_clients": len(self._db_clients),
            "registered_tenants": len(self._tenant_db_map),
            "db_usage": {db: list(tenants) for db, tenants in self._db_usage.items()},
        }


# 全局缓存管理器实例
_cache_manager: TenantCacheManager | None = None


def get_cache_manager() -> TenantCacheManager:
    """
    获取全局缓存管理器实例

    Returns:
        TenantCacheManager: 缓存管理器实例
    """
    global _cache_manager
    if _cache_manager is None:
        raise RuntimeError("TenantCacheManager 未初始化")
    return _cache_manager


def init_cache_manager(default_client: Redis) -> TenantCacheManager:
    """
    初始化缓存管理器

    Args:
        default_client: 默认 Redis 客户端

    Returns:
        TenantCacheManager: 缓存管理器实例
    """
    global _cache_manager
    _cache_manager = TenantCacheManager(default_client)
    return _cache_manager
