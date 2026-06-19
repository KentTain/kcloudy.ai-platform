"""提供第三方扩展相关功能。"""

from collections.abc import Callable
from typing import Annotated

from pydantic import Field
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket


# 创建一个包装函数来避免类型错误
async def _safe_evalsha(redis_client, script_sha, *args):
    """安全执行evalsha，避免类型错误"""
    return await redis_client.evalsha(script_sha, *args)


class TooManyRequestsError(Exception):
    """请求频率过高错误"""

    def __init__(self, expire: int):
        """
        初始化实例。

        Args:
            expire (int): expire 参数。
        """
        self.expire = expire
        super().__init__(f"请求频率过高，{expire}秒后重试")


class RateLimiter:
    """封装第三方扩展中的RateLimiter逻辑。"""

    def __init__(
        self,
        times: Annotated[int, Field(ge=0)] = 1,
        milliseconds: Annotated[int, Field(ge=-1)] = 0,
        seconds: Annotated[int, Field(ge=-1)] = 0,
        minutes: Annotated[int, Field(ge=-1)] = 0,
        hours: Annotated[int, Field(ge=-1)] = 0,
        identifier: Callable | None = None,
        callback: Callable | None = None,
    ):
        """
        初始化实例。

        Args:
            times (Annotated[int, Field(ge=0)]): times 参数。
            milliseconds (Annotated[int, Field(ge=-1)]): milliseconds 参数。
            seconds (Annotated[int, Field(ge=-1)]): seconds 参数。
            minutes (Annotated[int, Field(ge=-1)]): minutes 参数。
            hours (Annotated[int, Field(ge=-1)]): hours 参数。
            identifier (Callable | None): identifier 参数。
            callback (Callable | None): callback 参数。
        """
        self.times = times
        self.milliseconds = (
            milliseconds + 1000 * seconds + 60000 * minutes + 3600000 * hours
        )
        self.identifier = identifier
        self.callback = callback

    async def _check(self, key):
        # 导入在方法内部避免循环导入
        """
        处理check。

        Args:
            key: key 参数。

        Returns:
            处理结果。
        """
        from extended.fastapi.limiter import FastAPILimiter

        redis = FastAPILimiter.redis
        if not redis:
            raise Exception("Redis client is not initialized!")

        if not FastAPILimiter.lua_sha:
            raise Exception("Lua script not loaded!")

        # 使用包装函数来避免类型错误
        pexpire = await _safe_evalsha(
            redis,
            FastAPILimiter.lua_sha,
            1,
            key,
            str(self.times),
            str(self.milliseconds),
        )
        return pexpire

    async def __call__(self, request: Request, response: Response):
        # 导入在方法内部避免循环导入
        """
        实现 __call__ 协议方法。

        Args:
            request (Request): request 参数。
            response (Response): response 参数。

        Returns:
            处理结果。
        """
        from extended.fastapi.limiter import FastAPILimiter

        if not FastAPILimiter.redis:
            raise Exception(
                "You must call FastAPILimiter.init in startup event of fastapi!"
            )
        route_index = 0
        dep_index = 0
        for i, route in enumerate(request.app.routes):
            if route.path == request.scope["path"] and request.method in route.methods:
                route_index = i
                for j, dependency in enumerate(route.dependencies):
                    if self is dependency.dependency:
                        dep_index = j
                        break

        # moved here because constructor run before app startup
        identifier = self.identifier or FastAPILimiter.identifier
        callback = self.callback or FastAPILimiter.http_callback

        if not identifier or not callback:
            raise Exception("Identifier or callback is not set!")

        rate_key = await identifier(request)
        key = f"{FastAPILimiter.prefix}:{rate_key}:{route_index}:{dep_index}"
        try:
            pexpire = await self._check(key)
        except Exception:
            # 处理脚本不存在的错误
            if FastAPILimiter.redis and FastAPILimiter.lua_script:
                lua_script_result = await FastAPILimiter.redis.script_load(
                    FastAPILimiter.lua_script
                )
                FastAPILimiter.lua_sha = lua_script_result
                pexpire = await self._check(key)
            else:
                raise
        if pexpire != 0:
            return await callback(request, response, pexpire)


class WebSocketRateLimiter(RateLimiter):
    """封装第三方扩展中的WebSocketRateLimiter逻辑。"""

    async def __call__(self, ws: WebSocket, context_key=""):
        # 导入在方法内部避免循环导入
        """
        实现 __call__ 协议方法。

        Args:
            ws (WebSocket): ws 参数。
            context_key: context_key 参数。

        Returns:
            处理结果。
        """
        from extended.fastapi.limiter import FastAPILimiter

        if not FastAPILimiter.redis:
            raise Exception(
                "You must call FastAPILimiter.init in startup event of fastapi!"
            )
        identifier = self.identifier or FastAPILimiter.identifier
        callback = self.callback or FastAPILimiter.ws_callback

        if not identifier or not callback:
            raise Exception("Identifier or callback is not set!")

        rate_key = await identifier(ws)
        key = f"{FastAPILimiter.prefix}:ws:{rate_key}:{context_key}"
        pexpire = await self._check(key)
        if pexpire != 0:
            return await callback(ws, pexpire)
