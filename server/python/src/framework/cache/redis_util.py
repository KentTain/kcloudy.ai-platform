"""
RedisUtil - 统一的 Redis 工具类

封装常用 Redis 操作，支持单机、集群、哨兵模式。
"""

from __future__ import annotations

from typing import Any, Optional
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError


class RedisUtil:
    """统一的 Redis 工具类，所有 Redis 操作通过此类"""

    _client: Optional[Redis] = None
    _pool: Optional[ConnectionPool] = None

    @classmethod
    async def init(cls, config: Any) -> None:
        """
        初始化 Redis 连接

        Args:
            config: Redis 配置对象，支持 single/cluster/sentinel 模式
        """
        if config.mode == "single":
            pool_kwargs = {
                "host": config.single.host,
                "port": config.single.port,
                "db": config.single.db,
                "decode_responses": True,
            }

            # 添加密码
            if hasattr(config.single, "password") and config.single.password:
                pool_kwargs["password"] = config.single.password

            # 添加连接池配置
            if hasattr(config.single, "connection_pool") and config.single.connection_pool is not None:
                if hasattr(config.single.connection_pool, "max_connections"):
                    pool_kwargs["max_connections"] = config.single.connection_pool.max_connections

            cls._pool = ConnectionPool(**pool_kwargs)
            cls._client = Redis(connection_pool=cls._pool)

    @classmethod
    async def close(cls) -> None:
        """关闭 Redis 连接"""
        if cls._client:
            await cls._client.aclose()
            cls._client = None
        if cls._pool:
            await cls._pool.aclose()
            cls._pool = None

    @classmethod
    def get_client(cls) -> Redis:
        """获取 Redis 客户端"""
        if cls._client is None:
            raise RuntimeError("Redis 客户端未初始化")
        return cls._client

    @classmethod
    def is_initialized(cls) -> bool:
        """检查 Redis 是否已初始化"""
        return cls._client is not None

    # =========================================================================
    # 字符串操作
    # =========================================================================

    @classmethod
    async def set(cls, key: str, value: str, ttl: Optional[int] = None, nx: bool = False) -> bool:
        """
        设置键值对

        Args:
            key: 键名
            value: 值
            ttl: 过期时间（秒），None 表示永不过期
            nx: 仅当键不存在时设置

        Returns:
            bool: 操作是否成功
        """
        return await cls.get_client().set(key, value, ex=ttl, nx=nx)

    @classmethod
    async def get(cls, key: str) -> Optional[str]:
        """
        获取键值

        Args:
            key: 键名

        Returns:
            str | None: 键值，不存在则返回 None
        """
        result = await cls.get_client().get(key)
        if result is None:
            return None
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return result

    @classmethod
    async def delete(cls, key: str) -> int:
        """
        删除键

        Args:
            key: 键名

        Returns:
            int: 删除的键数量
        """
        return await cls.get_client().delete(key)

    @classmethod
    async def exists(cls, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 键名

        Returns:
            bool: 键是否存在
        """
        return await cls.get_client().exists(key) > 0

    @classmethod
    async def expire(cls, key: str, ttl: int) -> bool:
        """
        设置键的过期时间

        Args:
            key: 键名
            ttl: 过期时间（秒）

        Returns:
            bool: 操作是否成功
        """
        return await cls.get_client().expire(key, ttl)

    @classmethod
    async def keys(cls, pattern: str) -> list[str]:
        """
        获取匹配模式的所有键

        Args:
            pattern: 匹配模式

        Returns:
            list[str]: 键列表
        """
        result = await cls.get_client().keys(pattern)
        return [k.decode() if isinstance(k, bytes) else k for k in result]

    @classmethod
    async def incr(cls, key: str, amount: int = 1) -> int:
        """
        递增

        Args:
            key: 键名
            amount: 递增量

        Returns:
            int: 递增后的值
        """
        return await cls.get_client().incrby(key, amount)

    @classmethod
    async def decr(cls, key: str, amount: int = 1) -> int:
        """
        递减

        Args:
            key: 键名
            amount: 递减量

        Returns:
            int: 递减后的值
        """
        return await cls.get_client().decrby(key, amount)

    # =========================================================================
    # Hash 操作
    # =========================================================================

    @classmethod
    async def hget(cls, name: str, key: str) -> Optional[str]:
        """获取 Hash 字段值"""
        result = await cls.get_client().hget(name, key)
        if result is None:
            return None
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return result

    @classmethod
    async def hset(cls, name: str, key: str, value: str) -> int:
        """设置 Hash 字段值"""
        return await cls.get_client().hset(name, key, value)

    @classmethod
    async def hdel(cls, name: str, key: str) -> int:
        """删除 Hash 字段"""
        return await cls.get_client().hdel(name, key)

    @classmethod
    async def hgetall(cls, name: str) -> dict[str, str]:
        """获取 Hash 所有字段"""
        result = await cls.get_client().hgetall(name)
        return {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in result.items()}

    @classmethod
    async def hexists(cls, name: str, key: str) -> bool:
        """检查 Hash 字段是否存在"""
        return await cls.get_client().hexists(name, key)

    # =========================================================================
    # List 操作
    # =========================================================================

    @classmethod
    async def lpush(cls, key: str, *values: str) -> int:
        """从左侧插入列表"""
        return await cls.get_client().lpush(key, *values)

    @classmethod
    async def rpush(cls, key: str, *values: str) -> int:
        """从右侧插入列表"""
        return await cls.get_client().rpush(key, *values)

    @classmethod
    async def lpop(cls, key: str) -> Optional[str]:
        """从左侧弹出"""
        result = await cls.get_client().lpop(key)
        if result is None:
            return None
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return result

    @classmethod
    async def rpop(cls, key: str) -> Optional[str]:
        """从右侧弹出"""
        result = await cls.get_client().rpop(key)
        if result is None:
            return None
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return result

    @classmethod
    async def llen(cls, key: str) -> int:
        """获取列表长度"""
        return await cls.get_client().llen(key)

    # =========================================================================
    # Set 操作
    # =========================================================================

    @classmethod
    async def sadd(cls, key: str, *values: str) -> int:
        """添加集合成员"""
        return await cls.get_client().sadd(key, *values)

    @classmethod
    async def srem(cls, key: str, *values: str) -> int:
        """移除集合成员"""
        return await cls.get_client().srem(key, *values)

    @classmethod
    async def smembers(cls, key: str) -> set[str]:
        """获取集合所有成员"""
        result = await cls.get_client().smembers(key)
        return {v.decode() if isinstance(v, bytes) else v for v in result}

    @classmethod
    async def sismember(cls, key: str, value: str) -> bool:
        """检查是否是集合成员"""
        return await cls.get_client().sismember(key, value)

    # =========================================================================
    # Stream 操作（用于队列）
    # =========================================================================

    @classmethod
    async def xadd(cls, stream: str, fields: dict[str, Any], id: str = "*") -> str:
        """添加 Stream 消息"""
        result = await cls.get_client().xadd(stream, fields, id=id)
        return result.decode() if isinstance(result, bytes) else result

    @classmethod
    async def xread(cls, streams: dict[str, str], count: int = 1, block: int | None = None) -> list:
        """读取 Stream 消息"""
        return await cls.get_client().xread(streams, count=count, block=block)

    @classmethod
    async def xreadgroup(
        cls,
        groupname: str,
        consumername: str,
        streams: dict[str, str],
        count: int = 1,
        block: int | None = None
    ) -> list:
        """使用消费者组读取 Stream 消息"""
        return await cls.get_client().xreadgroup(
            groupname=groupname,
            consumername=consumername,
            streams=streams,
            count=count,
            block=block
        )

    @classmethod
    async def xack(cls, stream: str, group: str, *ids: str) -> int:
        """确认 Stream 消息"""
        return await cls.get_client().xack(stream, group, *ids)

    @classmethod
    async def xgroup_create(cls, stream: str, group: str, id: str = "0", mkstream: bool = False) -> bool:
        """创建消费者组"""
        try:
            await cls.get_client().xgroup_create(stream, group, id=id, mkstream=mkstream)
            return True
        except Exception:
            return False

    @classmethod
    async def xinfo_stream(cls, stream: str) -> dict:
        """获取 Stream 信息"""
        return await cls.get_client().xinfo_stream(stream)

    # =========================================================================
    # Pub/Sub 操作
    # =========================================================================

    @classmethod
    async def publish(cls, channel: str, message: str) -> int:
        """发布消息"""
        return await cls.get_client().publish(channel, message)

    @classmethod
    async def pubsub_numsub(cls, *channels: str) -> dict[str, int]:
        """获取频道订阅者数量"""
        result = await cls.get_client().pubsub_numsub(*channels)
        return {k.decode() if isinstance(k, bytes) else k: v for k, v in result}

    # =========================================================================
    # Lua 脚本
    # =========================================================================

    @classmethod
    async def eval(cls, script: str, numkeys: int, *args: Any) -> Any:
        """执行 Lua 脚本"""
        return await cls.get_client().eval(script, numkeys, *args)

    # =========================================================================
    # 健康检查
    # =========================================================================

    @classmethod
    async def health_check(cls) -> bool:
        """
        健康检查

        Returns:
            bool: 连接是否正常
        """
        try:
            await cls.get_client().ping()
            return True
        except (RedisError, ConnectionError, OSError):
            return False
