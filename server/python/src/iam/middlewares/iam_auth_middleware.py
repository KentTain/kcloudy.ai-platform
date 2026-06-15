"""
IAM 认证中间件

提供 Token 验证、用户信息注入、租户归属验证功能。
"""

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from framework.common.ctx import get_context
from iam.services import auth_service

_logger = logger.bind(name=__name__)


class IAMAuthMiddleware(BaseHTTPMiddleware):
    """IAM 认证中间件

    功能：
    1. 验证 JWT Token
    2. 验证用户租户归属
    3. 同步用户信息到 Context 和 request.state
    """

    # 需要认证的路径前缀（模块优先路由）
    PATH_PREFIXES = [
        "/iam/",
        "/ai/",
        "/tenant/console/",  # tenant 的 console 层也使用 IAM 认证
    ]

    # 不需要认证的路径（精确匹配或前缀匹配）
    EXEMPT_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        # IAM 认证公开接口
        "/iam/console/v1/auth/login",
        "/iam/console/v1/auth/register",
        "/iam/console/v1/auth/token/refresh",
        "/iam/console/v1/oauth/",
        # 内部接口豁免（模块间调用）
        "/iam/inner/",
        "/ai/inner/",
        "/tenant/inner/",
    }

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查是否已被其他认证中间件处理（如 AdminAuthMiddleware）
        if getattr(request.state, "authenticated", False):
            return await call_next(request)

        # 检查是否在认证路径范围内
        if not self._is_auth_path(request.url.path):
            return await call_next(request)

        # 检查是否为豁免路径
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # 获取 Token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return await self._unauthorized("未提供认证令牌")

        access_token = auth_header[7:]

        # 验证 Token
        payload = await auth_service.verify_access_token(access_token)
        if not payload:
            return await self._unauthorized("认证令牌无效或已过期")

        # 验证租户归属
        ctx = get_context()
        token_tenant_id = payload.get("tenant_id")
        if token_tenant_id and ctx.tenant_id and ctx.tenant_id != token_tenant_id:
            _logger.warning(
                f"跨租户访问被拒绝: user_tenant={token_tenant_id}, "
                f"current_tenant={ctx.tenant_id}"
            )
            return await self._forbidden("跨租户访问被拒绝")

        request.state.authenticated = True
        # 同步用户信息到 Context（主要数据源）
        ctx.session_id = payload.get("session_id")
        ctx.user_id = payload.get("user_id")
        ctx.user_name = payload.get("user_name")
        ctx.roles = payload.get("roles", [])
        ctx.permissions = payload.get("permissions", [])

        # 同时注入 request.state（保持向后兼容）
        # request.state.user_id = ctx.user_id
        # request.state.session_id = ctx.session_id
        # request.state.roles = ctx.roles
        # request.state.permissions = ctx.permissions

        return await call_next(request)

    def _is_auth_path(self, path: str) -> bool:
        """检查是否在认证路径范围内"""
        for prefix in self.PATH_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    def _is_exempt_path(self, path: str) -> bool:
        """检查是否为豁免路径"""
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        return False

    async def _unauthorized(self, message: str):
        """返回 401 响应"""
        from fastapi.responses import ORJSONResponse

        return ORJSONResponse(
            status_code=401,
            content={
                "code": 401,
                "msg": message,
                "data": None,
            },
        )

    async def _forbidden(self, message: str):
        """返回 403 响应"""
        from fastapi.responses import ORJSONResponse

        return ORJSONResponse(
            status_code=403,
            content={
                "code": 403,
                "msg": message,
                "data": None,
            },
        )


def require_permission(permission_code: str):
    """
    权限检查装饰器

    Args:
        permission_code: 需要的权限编码
    """

    def decorator(func):
        async def wrapper(*args, request: Request = None, **kwargs):
            # 从 Context 获取用户信息
            from framework.common.ctx import get_user_id

            user_id = get_user_id()
            if not user_id:
                from fastapi import HTTPException

                raise HTTPException(status_code=401, detail="未登录")

            # 检查权限
            from iam.services import permission_check_service

            has_perm = await permission_check_service.has_permission(
                user_id, permission_code
            )
            if not has_perm:
                from fastapi import HTTPException

                raise HTTPException(status_code=403, detail="权限不足")

            return await func(*args, request=request, **kwargs)

        return wrapper

    return decorator
