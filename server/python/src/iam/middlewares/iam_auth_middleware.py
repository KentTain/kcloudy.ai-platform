"""
IAM 认证中间件

提供 Token 验证和用户信息注入功能。
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from services.iam import auth_service
from framework.utils.jwt import decode_token


class IAMAuthMiddleware(BaseHTTPMiddleware):
    """IAM 认证中间件"""

    # 不需要认证的路径
    EXEMPT_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/iam/auth/login",
        "/api/v1/iam/auth/register",
        "/api/v1/iam/auth/token/refresh",
        "/api/v1/iam/oauth/",
    }

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查是否需要认证
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

        # 将用户信息注入请求
        request.state.user_id = payload.get("user_id")
        request.state.session_id = payload.get("session_id")
        request.state.roles = payload.get("roles", [])
        request.state.permissions = payload.get("permissions", [])

        return await call_next(request)

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


def require_permission(permission_code: str):
    """
    权限检查装饰器

    Args:
        permission_code: 需要的权限编码
    """
    def decorator(func):
        async def wrapper(*args, request: Request = None, **kwargs):
            user_id = getattr(request.state, "user_id", None) if request else None
            if not user_id:
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="未登录")

            # 检查权限
            from services.iam import permission_check_service
            has_perm = await permission_check_service.has_permission(user_id, permission_code)
            if not has_perm:
                from fastapi import HTTPException
                raise HTTPException(status_code=403, detail="权限不足")

            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator
