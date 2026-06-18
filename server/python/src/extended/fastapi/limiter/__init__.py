"""初始化第三方扩展包。"""

from math import ceil
from typing import Optional, Union
from collections.abc import Callable

import redis.asyncio as aioredis
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

from extended.fastapi.limiter.depends import TooManyRequestsError


async def default_identifier(request: Request | WebSocket):
    """
    处理default_identifier。

    Args:
        request (Request | WebSocket): request 参数。

    Returns:
        处理结果。
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0]
    else:
        ip = request.client.host if request.client else "127.0.0.1"
    return ip + ":" + request.scope["path"]


async def http_default_callback(request: Request, response: Response, pexpire: int):
    """
    处理http_default_callback。

    Args:
        request (Request): request 参数。
        response (Response): response 参数。
        pexpire (int): pexpire 参数。
    """
    expire = ceil(pexpire / 1000)
    raise TooManyRequestsError(expire)


async def ws_default_callback(ws: WebSocket, pexpire: int):
    """
    处理ws_default_callback。

    Args:
        ws (WebSocket): ws 参数。
        pexpire (int): pexpire 参数。
    """
    expire = ceil(pexpire / 1000)
    raise TooManyRequestsError(expire)


class FastAPILimiter:
    """封装第三方扩展中的FastAPILimiter逻辑。"""

    redis: aioredis.Redis | aioredis.RedisCluster | None = None
    prefix: str | None = None
    lua_sha: str = ""
    identifier: Callable | None = None
    http_callback: Callable | None = None
    ws_callback: Callable | None = None
    lua_script = """local key = KEYS[1]
local limit = tonumber(ARGV[1])
local expire_time = ARGV[2]

local current = tonumber(redis.call('get', key) or "0")
if current > 0 then
 if current + 1 > limit then
 return redis.call("PTTL",key)
 else
        redis.call("INCR", key)
 return 0
 end
else
    redis.call("SET", key, 1,"px",expire_time)
 return 0
end"""

    @classmethod
    async def init(
        cls,
        redis: aioredis.Redis | aioredis.RedisCluster,
        prefix: str = "fastapi-limiter",
        identifier: Callable = default_identifier,
        http_callback: Callable = http_default_callback,
        ws_callback: Callable = ws_default_callback,
    ) -> None:
        """
        处理init。

        Args:
            redis (aioredis.Redis | aioredis.RedisCluster): redis 参数。
            prefix (str): prefix 参数。
            identifier (Callable): identifier 参数。
            http_callback (Callable): http_callback 参数。
            ws_callback (Callable): ws_callback 参数。
        """
        cls.redis = redis
        cls.prefix = prefix
        cls.identifier = identifier
        cls.http_callback = http_callback
        cls.ws_callback = ws_callback
        cls.lua_sha = await redis.script_load(cls.lua_script)

    @classmethod
    async def close(cls) -> None:
        """关闭close。"""
        if cls.redis:
            await cls.redis.close()
