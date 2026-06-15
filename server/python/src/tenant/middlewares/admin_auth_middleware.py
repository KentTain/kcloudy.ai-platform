"""
管理员认证中间件

为管理后台提供独立的超级管理员认证体系。
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Callable
import secrets

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from tenant.models import TenantAdmin
from framework.database.core.engine import async_session
from framework.utils.crypto import hash_password, verify_password
from sqlalchemy import select

if TYPE_CHECKING:
    from starlette.types import ASGIApp

_logger = logger.bind(name=__name__)

# 管理后台路径前缀
ADMIN_PATH_PREFIX = "/admin/"

# 租户级管理 API 路径前缀（使用租户用户 JWT token，而非管理员 token）
TENANT_ADMIN_API_PREFIXES = [
    "/admin/v1/iam",
    "/admin/v1/system-settings",
]

# Token 存储简化版（生产环境应使用 Redis）
_admin_tokens: dict[str, dict] = {}
# Token 过期时间（小时）
TOKEN_EXPIRE_HOURS = 24


def generate_token() -> str:
    """生成访问令牌"""
    return secrets.token_urlsafe(32)


class AdminAuthService:
    """管理员认证服务"""

    @staticmethod
    async def login(username: str, password: str) -> tuple[str, TenantAdmin] | None:
        """
        管理员登录

        场景：管理员登录
        WHEN 超级管理员使用正确的用户名和密码登录
        THEN 返回管理员 Token
        """
        async with async_session() as session:
            stmt = select(TenantAdmin).where(
                TenantAdmin.username == username,
                TenantAdmin.is_active == True
            )
            result = await session.execute(stmt)
            admin = result.scalar_one_or_none()

            if not admin:
                return None

            if not verify_password(password, admin.password):
                return None

            # 生成 Token
            token = generate_token()
            _admin_tokens[token] = {
                "admin_id": admin.id,
                "username": admin.username,
                "is_default": admin.is_default,
                "expires_at": datetime.now() + timedelta(hours=TOKEN_EXPIRE_HOURS)
            }

            return token, admin

    @staticmethod
    def verify_token(token: str) -> dict | None:
        """验证 Token"""
        if token not in _admin_tokens:
            return None

        token_data = _admin_tokens[token]
        if datetime.now() > token_data["expires_at"]:
            del _admin_tokens[token]
            return None

        return token_data

    @staticmethod
    def logout(token: str) -> bool:
        """登出"""
        if token in _admin_tokens:
            del _admin_tokens[token]
            return True
        return False


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """
    管理员认证中间件

    场景：非管理员访问被拒绝
    WHEN 普通用户尝试访问管理后台 API
    THEN 返回 HTTP 403 错误

    场景：无 Token 访问被拒绝
    WHEN 未携带 Token 访问管理后台 API
    THEN 返回 HTTP 401 错误
    """

    def __init__(self, app: "ASGIApp"):
        super().__init__(app)
        self._security = HTTPBearer(auto_error=False)

    async def dispatch(self, request: "Request", call_next: Callable):
        """处理请求"""
        # 检查是否是管理后台路径
        if not request.url.path.startswith(ADMIN_PATH_PREFIX):
            return await call_next(request)

        # 租户级管理 API 跳过管理员认证（由 IAMAuthMiddleware 处理）
        for prefix in TENANT_ADMIN_API_PREFIXES:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        # 登录接口跳过认证，标记为已认证
        if request.url.path == "/admin/v1/auth/login":
            request.state.authenticated = True
            return await call_next(request)

        try:
            # 提取 Token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return self._error_response(401, "未提供认证令牌")

            token = auth_header.replace("Bearer ", "")

            # 验证 Token
            token_data = AdminAuthService.verify_token(token)
            if not token_data:
                return self._error_response(401, "无效或过期的令牌")

            # 注入管理员信息到请求状态
            request.state.admin = token_data
            request.state.authenticated = True  # 标记已认证，供后续中间件识别

            return await call_next(request)

        except Exception as e:
            _logger.exception("管理员认证中间件处理异常")
            return self._error_response(500, str(e))

    def _error_response(self, status_code: int, message: str) -> JSONResponse:
        """生成错误响应"""
        return JSONResponse(
            status_code=status_code,
            content={"code": status_code, "message": message, "data": None},
        )


# 依赖注入：获取当前管理员
async def get_current_admin(request: Request) -> dict:
    """获取当前登录的管理员"""
    admin = getattr(request.state, "admin", None)
    if not admin:
        raise HTTPException(status_code=401, detail="未认证")
    return admin
