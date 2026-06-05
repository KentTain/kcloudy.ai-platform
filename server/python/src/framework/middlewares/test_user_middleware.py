"""
测试用户中间件

提供开发测试环境下的用户模拟功能。
仅用于非生产环境，通过 X-Test-User-Id 请求头注入测试用户。
"""

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from framework.common.ctx import get_context

_logger = logger.bind(name=__name__)


class TestUserMiddleware(BaseHTTPMiddleware):
    """测试用户中间件

    功能：
    1. 仅在非生产环境生效
    2. 支持 X-Test-User-Id 请求头
    3. 覆盖用户信息到 Context

    注意：此中间件必须最后注册（最先执行），以便在认证中间件之后覆盖用户信息。
    """

    def __init__(self, app: ASGIApp, enabled: bool = False, env: str = "development"):
        super().__init__(app)
        self.enabled = enabled
        self.env = env

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 执行后续处理（先通过认证中间件）
        response = await call_next(request)

        # 仅在非生产环境且启用时生效
        if not self.enabled or self.env == "production":
            return response

        # 检查测试用户头
        test_user_id = request.headers.get("X-Test-User-Id")
        if test_user_id:
            ctx = get_context()
            ctx.user_id = test_user_id
            _logger.warning(
                f"[TEST MODE] 使用测试用户: {test_user_id} "
                f"(仅用于开发测试，请勿在生产环境使用)"
            )

        return response
