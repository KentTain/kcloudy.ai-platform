"""
租户感知的 Redis 工具类

在原有 RedisUtil 基础上，自动注入租户前缀。
"""

from __future__ import annotations

from typing import Any, Optional

from framework.cache.redis_util import RedisUtil
from framework.tenant.context import get_tenant_id
from framework.database.mixins.tenant import should_skip_tenant


# 租户前缀格式
TENANT_KEY_PREFIX = "{tenant_id}:{key}"
TENANT_QUEUE_PREFIX = "{tenant_id}:queue:{queue_name}"
TENANT_CHANNEL_PREFIX = "{tenant_id}:channel:{channel_name}"
TENANT_LOCK_PREFIX = "{tenant_id}:lock:{lock_key}"


def _get_tenant_prefix() -> str | None:
    """获取租户前缀，如果跳过或无租户则返回 None"""
    if should_skip_tenant():
        return None
    return get_tenant_id()


def _build_key(key: str, skip_tenant: bool = False) -> str:
    """构建带租户前缀的 Key"""
    if skip_tenant or should_skip_tenant():
        return key

    tenant_id = get_tenant_id()
    if tenant_id:
        return TENANT_KEY_PREFIX.format(tenant_id=tenant_id, key=key)
    return key


def _build_stream_key(queue_name: str, skip_tenant: bool = False) -> str:
    """构建带租户前缀的 Stream Key"""
    if skip_tenant or should_skip_tenant():
        return f"queue:{queue_name}"

    tenant_id = get_tenant_id()
    if tenant_id:
        return TENANT_QUEUE_PREFIX.format(tenant_id=tenant_id, queue_name=queue_name)
    return f"queue:{queue_name}"


def _build_channel(channel_name: str, skip_tenant: bool = False) -> str:
    """构建带租户前缀的 Channel"""
    if skip_tenant or should_skip_tenant():
        return channel_name

    tenant_id = get_tenant_id()
    if tenant_id:
        return TENANT_CHANNEL_PREFIX.format(tenant_id=tenant_id, channel_name=channel_name)
    return channel_name


def _build_lock_key(lock_key: str, skip_tenant: bool = False) -> str:
    """构建带租户前缀的 Lock Key"""
    if skip_tenant or should_skip_tenant():
        return f"lock:{lock_key}"

    tenant_id = get_tenant_id()
    if tenant_id:
        return TENANT_LOCK_PREFIX.format(tenant_id=tenant_id, lock_key=lock_key)
    return f"lock:{lock_key}"


class TenantRedisUtil:
    """
    租户感知的 Redis 工具类

    自动为所有 Key、队列、频道、锁添加租户前缀。

    使用示例：
        # 设置缓存（自动添加租户前缀）
        await TenantRedisUtil.set("user:123", data)
        # 实际 Key: "tenant_001:user:123"

        # 跳过租户前缀（管理员场景）
        await TenantRedisUtil.set("system:config", data, skip_tenant=True)
        # 实际 Key: "system:config"
    """

    # =========================================================================
    # 字符串操作
    # =========================================================================

    @classmethod
    async def set(
        cls, key: str, value: str, ttl: Optional[int] = None,
        nx: bool = False, skip_tenant: bool = False
    ) -> bool:
        """设置键值对，自动添加租户前缀"""
        actual_key = _build_key(key, skip_tenant)
        return await RedisUtil.set(actual_key, value, ttl=ttl, nx=nx)

    @classmethod
    async def get(cls, key: str, skip_tenant: bool = False) -> Optional[str]:
        """获取键值，自动添加租户前缀"""
        actual_key = _build_key(key, skip_tenant)
        return await RedisUtil.get(actual_key)

    @classmethod
    async def delete(cls, key: str, skip_tenant: bool = False) -> int:
        """删除键，自动添加租户前缀"""
        actual_key = _build_key(key, skip_tenant)
        return await RedisUtil.delete(actual_key)

    @classmethod
    async def exists(cls, key: str, skip_tenant: bool = False) -> bool:
        """检查键是否存在，自动添加租户前缀"""
        actual_key = _build_key(key, skip_tenant)
        return await RedisUtil.exists(actual_key)

    @classmethod
    async def expire(cls, key: str, ttl: int, skip_tenant: bool = False) -> bool:
        """设置键的过期时间，自动添加租户前缀"""
        actual_key = _build_key(key, skip_tenant)
        return await RedisUtil.expire(actual_key, ttl)

    @classmethod
    async def incr(cls, key: str, amount: int = 1, skip_tenant: bool = False) -> int:
        """递增，自动添加租户前缀"""
        actual_key = _build_key(key, skip_tenant)
        return await RedisUtil.incr(actual_key, amount)

    @classmethod
    async def decr(cls, key: str, amount: int = 1, skip_tenant: bool = False) -> int:
        """递减，自动添加租户前缀"""
        actual_key = _build_key(key, skip_tenant)
        return await RedisUtil.decr(actual_key, amount)

    # =========================================================================
    # Hash 操作
    # =========================================================================

    @classmethod
    async def hget(cls, name: str, key: str, skip_tenant: bool = False) -> Optional[str]:
        """获取 Hash 字段值，自动添加租户前缀"""
        actual_name = _build_key(name, skip_tenant)
        return await RedisUtil.hget(actual_name, key)

    @classmethod
    async def hset(cls, name: str, key: str, value: str, skip_tenant: bool = False) -> int:
        """设置 Hash 字段值，自动添加租户前缀"""
        actual_name = _build_key(name, skip_tenant)
        return await RedisUtil.hset(actual_name, key, value)

    @classmethod
    async def hdel(cls, name: str, key: str, skip_tenant: bool = False) -> int:
        """删除 Hash 字段，自动添加租户前缀"""
        actual_name = _build_key(name, skip_tenant)
        return await RedisUtil.hdel(actual_name, key)

    @classmethod
    async def hgetall(cls, name: str, skip_tenant: bool = False) -> dict[str, str]:
        """获取 Hash 所有字段，自动添加租户前缀"""
        actual_name = _build_key(name, skip_tenant)
        return await RedisUtil.hgetall(actual_name)

    # =========================================================================
    # Stream 操作（队列）
    # =========================================================================

    @classmethod
    async def xadd(
        cls, queue_name: str, fields: dict[str, Any],
        id: str = "*", skip_tenant: bool = False
    ) -> str:
        """添加 Stream 消息，自动添加租户前缀"""
        actual_stream = _build_stream_key(queue_name, skip_tenant)
        return await RedisUtil.xadd(actual_stream, fields, id=id)

    @classmethod
    async def xread(
        cls, queue_names: list[str], count: int = 1,
        block: int | None = None, skip_tenant: bool = False
    ) -> list:
        """读取 Stream 消息，自动添加租户前缀"""
        actual_streams = {
            _build_stream_key(q, skip_tenant): "0"
            for q in queue_names
        }
        return await RedisUtil.xread(actual_streams, count=count, block=block)

    @classmethod
    async def xreadgroup(
        cls, groupname: str, consumername: str,
        queue_name: str, count: int = 1,
        block: int | None = None, skip_tenant: bool = False
    ) -> list:
        """使用消费者组读取 Stream 消息，自动添加租户前缀"""
        actual_stream = _build_stream_key(queue_name, skip_tenant)
        return await RedisUtil.xreadgroup(
            groupname=groupname,
            consumername=consumername,
            streams={actual_stream: ">"},
            count=count,
            block=block
        )

    @classmethod
    async def xack(
        cls, queue_name: str, group: str,
        *ids: str, skip_tenant: bool = False
    ) -> int:
        """确认 Stream 消息，自动添加租户前缀"""
        actual_stream = _build_stream_key(queue_name, skip_tenant)
        return await RedisUtil.xack(actual_stream, group, *ids)

    @classmethod
    async def xgroup_create(
        cls, queue_name: str, group: str,
        id: str = "0", mkstream: bool = False,
        skip_tenant: bool = False
    ) -> bool:
        """创建消费者组，自动添加租户前缀"""
        actual_stream = _build_stream_key(queue_name, skip_tenant)
        return await RedisUtil.xgroup_create(actual_stream, group, id=id, mkstream=mkstream)

    # =========================================================================
    # Pub/Sub 操作
    # =========================================================================

    @classmethod
    async def publish(
        cls, channel: str, message: str, skip_tenant: bool = False
    ) -> int:
        """发布消息，自动添加租户前缀"""
        actual_channel = _build_channel(channel, skip_tenant)
        return await RedisUtil.publish(actual_channel, message)

    # =========================================================================
    # 分布式锁
    # =========================================================================

    @classmethod
    async def acquire_lock(
        cls, lock_key: str, ttl: int = 30,
        skip_tenant: bool = False
    ) -> bool:
        """
        获取分布式锁，自动添加租户前缀

        Args:
            lock_key: 锁标识
            ttl: 锁过期时间（秒）
            skip_tenant: 是否跳过租户前缀

        Returns:
            bool: 是否获取成功
        """
        actual_key = _build_lock_key(lock_key, skip_tenant)
        # 使用 SET NX 实现简单的分布式锁
        return await RedisUtil.set(actual_key, "1", ttl=ttl, nx=True)

    @classmethod
    async def release_lock(cls, lock_key: str, skip_tenant: bool = False) -> bool:
        """
        释放分布式锁，自动添加租户前缀

        Args:
            lock_key: 锁标识
            skip_tenant: 是否跳过租户前缀

        Returns:
            bool: 是否释放成功
        """
        actual_key = _build_lock_key(lock_key, skip_tenant)
        result = await RedisUtil.delete(actual_key)
        return result > 0

    # =========================================================================
    # 健康检查
    # =========================================================================

    @classmethod
    async def health_check(cls) -> bool:
        """健康检查"""
        return await RedisUtil.health_check()


# 便捷函数
async def tenant_redis_set(key: str, value: str, ttl: int | None = None, skip_tenant: bool = False) -> bool:
    """设置租户缓存"""
    return await TenantRedisUtil.set(key, value, ttl=ttl, skip_tenant=skip_tenant)


async def tenant_redis_get(key: str, skip_tenant: bool = False) -> str | None:
    """获取租户缓存"""
    return await TenantRedisUtil.get(key, skip_tenant=skip_tenant)


async def tenant_redis_delete(key: str, skip_tenant: bool = False) -> int:
    """删除租户缓存"""
    return await TenantRedisUtil.delete(key, skip_tenant=skip_tenant)
