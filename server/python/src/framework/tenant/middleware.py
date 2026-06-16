"""
租户中间件

自动解析租户标识、验证租户状态、注入租户上下文。
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from framework.tenant.context import TenantContext
from framework.tenant.exceptions import (
    TenantAccessDeniedError,
    TenantError,
    TenantExpiredError,
    TenantInactiveError,
    TenantNotFoundError,
    TenantResolveError,
)
from framework.tenant.protocols import get_tenant_provider
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
    "/tenant/admin/",  # 管理后台不经过租户中间件
    # IAM Console 层公开接口
    "/iam/console/v1/auth/login",
    "/iam/console/v1/auth/register",
    "/iam/console/v1/auth/token/refresh",
    "/iam/console/v1/oauth/",
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

    注意：用户信息由 IAMAuthMiddleware 设置，不再在此处理测试用户。
    """

    def __init__(self, app: "ASGIApp", *, extra_skip_paths: list[str] | None = None):
        """初始化租户中间件

        Args:
            app: ASGI 应用
            extra_skip_paths: 扩展的跳过路径列表（追加到内置 SKIP_PATHS 之后）
        """
        super().__init__(app)
        # 合并内置路径和扩展路径
        self.skip_paths = SKIP_PATHS + (extra_skip_paths or [])

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
                    TenantResolveError(
                        "无法解析租户标识，请在请求头中提供 X-Tenant-Id"
                    ),
                    400,
                )

            # 加载租户信息并验证
            tenant = await self._load_and_validate_tenant(tenant_id, request)

            # 注入租户上下文
            TenantContext.set_current_tenant(tenant)

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
        if path == "/":
            return True

        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return True
        return False

    async def _load_and_validate_tenant(self, tenant_id: str, request: "Request"):
        """加载租户信息并验证状态"""
        # 通过 TenantProvider 获取租户
        provider = get_tenant_provider()
        if not provider:
            raise TenantError("TenantProvider 未注册")

        tenant = await provider.get_tenant(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"租户不存在: {tenant_id}")

        # 验证租户状态
        self._validate_tenant_access(tenant, request, provider)

        return tenant

    def _validate_tenant_access(self, tenant, request: "Request", provider) -> None:
        """验证租户访问权限"""
        # 检查租户状态
        if tenant.status != "active":
            raise TenantInactiveError(f"租户已停用: {tenant.name}")

        # 检查过期时间
        if tenant.expired_at and tenant.expired_at < datetime.now(timezone.utc):
            raise TenantExpiredError(f"租户已过期: {tenant.name}")

    def _error_response(
        self, error: TenantError, status_code: int | None = None
    ) -> JSONResponse:
        """生成错误响应"""
        status_code = status_code or self._get_error_status_code(error)
        return JSONResponse(
            status_code=status_code,
            content={
                "code": status_code,
                "message": str(error),
                "data": None,
            },
        )

    def _get_error_status_code(self, error: TenantError) -> int:
        """获取错误状态码"""
        if isinstance(error, TenantNotFoundError):
            return 404
        if isinstance(error, TenantAccessDeniedError):
            return 403
        if isinstance(error, TenantInactiveError | TenantExpiredError):
            return 403
        return 400
