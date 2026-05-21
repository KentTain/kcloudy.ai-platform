"""
租户中间件

自动解析租户标识、验证租户状态、注入租户上下文。
"""

from datetime import datetime
from typing import TYPE_CHECKING, Callable

from loguru import logger
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from framework.database.core.engine import async_session
from demo.models.tenant import Tenant, TenantStatus
from framework.common.ctx import set_context, Context
from framework.tenant.context import TenantContext, SimpleTenant
from framework.tenant.exceptions import (
    TenantAccessDeniedError,
    TenantError,
    TenantExpiredError,
    TenantInactiveError,
    TenantNotFoundError,
    TenantResolveError,
)
from framework.tenant.resolver import TenantResolver

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.types import ASGIApp

_logger = logger.bind(name=__name__)

# 跳过租户中间件的路径前缀
SKIP_PATHS = [
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/admin/",  # 管理后台不经过租户中间件
]


class TenantMiddleware(BaseHTTPMiddleware):
    """租户中间件

    处理流程：
    1. 检查是否跳过租户验证
    2. 解析租户标识
    3. 加载租户信息
    4. 验证租户状态
    5. 注入租户上下文
    6. 请求结束后清理上下文
    """

    def __init__(self, app: "ASGIApp", *, skip_paths: list[str] | None = None):
        super().__init__(app)
        self.skip_paths = skip_paths or SKIP_PATHS

    async def dispatch(self, request: "Request", call_next: Callable):
        """处理请求"""
        # 检查是否跳过租户验证
        if self._should_skip(request):
            return await call_next(request)

        try:
            # 解析租户标识
            tenant_id = TenantResolver.resolve(request)

            # 如果没有解析到租户标识，返回错误
            if not tenant_id:
                return self._error_response(
                    TenantResolveError("无法解析租户标识，请在请求头中提供 X-Tenant-Id"),
                    400,
                )

            # 加载租户信息并验证
            tenant = await self._load_and_validate_tenant(tenant_id, request)

            # 注入租户上下文
            self._inject_context(tenant)

            # 执行后续处理
            response = await call_next(request)

            return response

        except TenantError as e:
            return self._error_response(e)
        except Exception as e:
            _logger.exception("租户中间件处理异常")
            return self._error_response(TenantError(str(e)), 500)
        finally:
            # 清理租户上下文
            TenantContext.clear()

    def _should_skip(self, request: "Request") -> bool:
        """检查是否跳过租户验证"""
        path = request.url.path
        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return True
        return False

    async def _load_and_validate_tenant(
        self, tenant_id: str, request: "Request"
    ) -> Tenant:
        """加载租户信息并验证状态"""
        async with async_session() as session:
            # 查询租户
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()

            # 验证租户存在
            if not tenant:
                raise TenantNotFoundError(tenant_id)

            # 验证租户状态
            if tenant.status != TenantStatus.ACTIVE:
                raise TenantInactiveError(tenant_id)

            # 验证租户未过期
            if tenant.expired_at and tenant.expired_at < datetime.now():
                raise TenantExpiredError(tenant_id)

            # 验证用户有权访问该租户（如果有用户信息）
            await self._validate_tenant_access(tenant_id, request, session)

            return tenant

    async def _validate_tenant_access(
        self, tenant_id: str, request: "Request", session
    ) -> None:
        """验证用户有权访问租户

        如果请求中有用户信息，检查用户是否属于该租户。
        """
        from demo.models.tenant import UserTenant

        user_id = self._get_user_id(request)
        if not user_id:
            return

        # 检查用户-租户关联
        stmt = select(UserTenant).where(
            UserTenant.user_id == user_id, UserTenant.tenant_id == tenant_id
        )
        result = await session.execute(stmt)
        user_tenant = result.scalar_one_or_none()

        if not user_tenant:
            raise TenantAccessDeniedError(tenant_id)

    def _get_user_id(self, request: "Request") -> str | None:
        """获取当前用户 ID"""
        user = getattr(request.state, "user", None)
        if user:
            if hasattr(user, "id"):
                return user.id
            if isinstance(user, dict) and "id" in user:
                return user["id"]
            if isinstance(user, dict) and "user_id" in user:
                return user["user_id"]
        return None

    def _inject_context(self, tenant: Tenant) -> None:
        """注入租户上下文"""
        # 设置租户上下文
        TenantContext.set_current_tenant(tenant)

        # 同时设置通用上下文（供数据库事件监听器使用）
        ctx = Context()
        ctx.tenant_id = tenant.id
        set_context(ctx)

    def _error_response(self, error: TenantError, status_code: int = None) -> JSONResponse:
        """生成错误响应"""
        code = status_code or self._get_error_status_code(error)
        return JSONResponse(
            status_code=code,
            content={"code": code, "message": error.message, "data": None},
        )

    def _get_error_status_code(self, error: TenantError) -> int:
        """根据异常类型获取 HTTP 状态码"""
        if isinstance(error, TenantNotFoundError):
            return 404
        elif isinstance(
            error, (TenantInactiveError, TenantExpiredError, TenantAccessDeniedError)
        ):
            return 403
        elif isinstance(error, TenantResolveError):
            return 400
        else:
            return 500


