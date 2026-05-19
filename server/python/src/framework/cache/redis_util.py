"""
RedisUtil - 统一的 Redis 工具类

封装常用 Redis 操作，支持单机、集群、哨兵模式。
"""

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
    async def set(cls, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        设置键值对

        Args:
            key: 键名
            value: 值
            ttl: 过期时间（秒），None 表示永不过期

        Returns:
            bool: 操作是否成功
        """
        return await cls._client.set(key, value, ex=ttl)

    @classmethod
    async def get(cls, key: str) -> Optional[str]:
        """
        获取键值

        Args:
            key: 键名

        Returns:
            str | None: 键值，不存在则返回 None
        """
        result = await cls._client.get(key)
        if result is None:
            return None
        # 解码 bytes 为 str
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
        return await cls._client.delete(key)

    @classmethod
    async def exists(cls, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 键名

        Returns:
            bool: 键是否存在
        """
        return await cls._client.exists(key) > 0

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
        return await cls._client.expire(key, ttl)

    @classmethod
    async def health_check(cls) -> bool:
        """
        健康检查

        Returns:
            bool: 连接是否正常
        """
        try:
            await cls._client.ping()
            return True
        except (RedisError, ConnectionError, OSError):
            return False
