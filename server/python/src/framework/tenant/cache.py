"""
租户缓存

实现两级缓存策略：L1 本地内存 + L2 Redis。
"""

from __future__ import annotations

import json
from collections import OrderedDict
from datetime import datetime
from typing import TYPE_CHECKING, Any
from threading import Lock

from loguru import logger

from framework.tenant.context import SimpleTenant

if TYPE_CHECKING:
    from framework.cache.redis_util import RedisUtil

_logger = logger.bind(name=__name__)

# 缓存 Key 前缀
TENANT_INFO_PREFIX = "tenant:info:"
TENANT_CONFIG_PREFIX = "tenant:config:"
TENANT_CACHE_INVALIDATE_CHANNEL = "tenant:cache:invalidate"

# 缓存配置
L1_MAX_SIZE = 1000
L2_TTL_SECONDS = 300  # 5 分钟


class TenantL1Cache:
    """
    租户 L1 本地缓存

    使用 LRU 策略，最大条目数 1000。
    """

    def __init__(self, max_size: int = L1_MAX_SIZE):
        self._cache: OrderedDict[str, SimpleTenant] = OrderedDict()
        self._max_size = max_size
        self._lock = Lock()

    def get(self, tenant_id: str) -> SimpleTenant | None:
        """获取缓存，命中时移动到末尾（LRU）"""
        with self._lock:
            if tenant_id in self._cache:
                # 移动到末尾（最近使用）
                self._cache.move_to_end(tenant_id)
                return self._cache[tenant_id]
            return None

    def set(self, tenant: SimpleTenant) -> None:
        """设置缓存，超过最大条目时淘汰最旧的"""
        with self._lock:
            if tenant.id in self._cache:
                # 已存在，更新并移动到末尾
                self._cache.move_to_end(tenant.id)
                self._cache[tenant.id] = tenant
            else:
                # 新增
                self._cache[tenant.id] = tenant
                # 超过最大条目时淘汰最旧的
                while len(self._cache) > self._max_size:
                    self._cache.popitem(last=False)

    def delete(self, tenant_id: str) -> None:
        """删除缓存"""
        with self._lock:
            self._cache.pop(tenant_id, None)

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """获取缓存条目数"""
        with self._lock:
            return len(self._cache)


class TenantCache:
    """
    租户两级缓存

    L1: 本地内存缓存（进程级）
    L2: Redis 缓存（跨实例共享）
    """

    _l1_cache: TenantL1Cache = TenantL1Cache()
    _redis: "RedisUtil | None" = None
    _pubsub_listener_started: bool = False

    @classmethod
    def init(cls, redis: "RedisUtil") -> None:
        """初始化缓存，设置 Redis 客户端"""
        cls._redis = redis
        cls._start_pubsub_listener()

    @classmethod
    async def get(cls, tenant_id: str) -> SimpleTenant | None:
        """
        获取租户信息

        查询顺序：L1 → L2 → 数据库
        """
        # L1: 本地缓存
        tenant = cls._l1_cache.get(tenant_id)
        if tenant:
            _logger.debug(f"L1 缓存命中: {tenant_id}")
            return tenant

        # L2: Redis 缓存
        if cls._redis:
            tenant = await cls._get_from_l2(tenant_id)
            if tenant:
                _logger.debug(f"L2 缓存命中: {tenant_id}")
                # 回填 L1
                cls._l1_cache.set(tenant)
                return tenant

        return None

    @classmethod
    async def set(cls, tenant: SimpleTenant) -> None:
        """设置租户缓存（L1 + L2）"""
        # 设置 L1
        cls._l1_cache.set(tenant)

        # 设置 L2
        if cls._redis:
            await cls._set_to_l2(tenant)

    @classmethod
    async def delete(cls, tenant_id: str) -> None:
        """删除租户缓存（L1 + L2）"""
        # 删除 L1
        cls._l1_cache.delete(tenant_id)

        # 删除 L2
        if cls._redis:
            await cls._delete_from_l2(tenant_id)

    @classmethod
    async def invalidate(cls, tenant_id: str) -> None:
        """
        使缓存失效

        清除本地缓存、Redis 缓存，并发布失效通知。
        """
        # 清除 L1
        cls._l1_cache.delete(tenant_id)

        # 清除 L2
        if cls._redis:
            await cls._delete_from_l2(tenant_id)
            # 发布失效通知
            await cls._redis.publish(
                TENANT_CACHE_INVALIDATE_CHANNEL,
                json.dumps({"tenant_id": tenant_id, "action": "invalidate"}),
            )

    @classmethod
    async def _get_from_l2(cls, tenant_id: str) -> SimpleTenant | None:
        """从 Redis 获取租户信息"""
        if not cls._redis:
            return None

        key = f"{TENANT_INFO_PREFIX}{tenant_id}"
        data = await cls._redis.get(key)
        if data:
            try:
                obj = json.loads(data)
                return SimpleTenant(
                    id=obj["id"],
                    name=obj["name"],
                    code=obj["code"],
                    status=obj["status"],
                )
            except (json.JSONDecodeError, KeyError) as e:
                _logger.warning(f"解析 Redis 缓存失败: {e}")
        return None

    @classmethod
    async def _set_to_l2(cls, tenant: SimpleTenant) -> None:
        """设置 Redis 缓存"""
        if not cls._redis:
            return

        key = f"{TENANT_INFO_PREFIX}{tenant.id}"
        data = json.dumps({
            "id": tenant.id,
            "name": tenant.name,
            "code": tenant.code,
            "status": tenant.status,
        })
        await cls._redis.set(key, data, ttl=L2_TTL_SECONDS)

    @classmethod
    async def _delete_from_l2(cls, tenant_id: str) -> None:
        """删除 Redis 缓存"""
        if not cls._redis:
            return

        key = f"{TENANT_INFO_PREFIX}{tenant_id}"
        await cls._redis.delete(key)

    @classmethod
    def _start_pubsub_listener(cls) -> None:
        """启动 Pub/Sub 监听器（用于缓存失效通知）"""
        if cls._pubsub_listener_started or not cls._redis:
            return

        cls._pubsub_listener_started = True
        # 注意：实际的 Pub/Sub 监听需要在异步环境中启动
        # 这里只是标记，实际启动在应用初始化时

    @classmethod
    def handle_invalidation_message(cls, message: str) -> None:
        """处理缓存失效消息"""
        try:
            data = json.loads(message)
            tenant_id = data.get("tenant_id")
            if tenant_id:
                cls._l1_cache.delete(tenant_id)
                _logger.debug(f"收到缓存失效通知，清除 L1: {tenant_id}")
        except json.JSONDecodeError:
            _logger.warning(f"无效的缓存失效消息: {message}")

    @classmethod
    def clear_all(cls) -> None:
        """清空所有本地缓存"""
        cls._l1_cache.clear()
