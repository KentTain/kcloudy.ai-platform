"""Redis 依赖注入

提供 Redis 客户端的 FastAPI 依赖注入。
"""

from redis.asyncio import Redis

from framework.cache.redis_util import RedisUtil


async def get_redis_client() -> Redis:
    """获取 Redis 客户端
    
    Returns:
        Redis: Redis 客户端实例
    """
    return RedisUtil._client
