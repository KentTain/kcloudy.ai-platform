"""
租户解析器

从请求中解析租户标识，支持多种解析策略。
"""

from typing import TYPE_CHECKING, Protocol

from framework.tenant.exceptions import TenantResolveError

if TYPE_CHECKING:
    from starlette.requests import Request


class TenantResolver:
    """租户解析器

    支持的解析策略（优先级从高到低）：
    1. 请求头 X-Tenant-Id
    2. Context 中的 tenant_id（由 TenantMiddleware 或 IAMAuthMiddleware 设置）
    3. request.state.user 中的 tenant_id（向后兼容）
    """

    HEADER_TENANT_ID = "X-Tenant-Id"

    @classmethod
    def resolve(cls, request: "Request") -> str | None:
        """解析租户标识

        Args:
            request: HTTP 请求对象

        Returns:
            租户 ID 或 None
        """
        # 优先级 1: 从请求头获取
        tenant_id = cls._resolve_from_header(request)
        if tenant_id:
            return tenant_id

        # 优先级 2: 从 Context 获取（主要数据源）
        tenant_id = cls._resolve_from_context()
        if tenant_id:
            return tenant_id

        return None

    @classmethod
    def _resolve_from_header(cls, request: "Request") -> str | None:
        """从请求头解析租户 ID"""
        return request.headers.get(cls.HEADER_TENANT_ID)

    @classmethod
    def _resolve_from_context(cls) -> str | None:
        """从 Context (ContextVar) 获取租户 ID

        Context 由以下中间件设置：
        - TenantMiddleware: 解析租户并设置到 Context
        - IAMAuthMiddleware: 验证用户并验证租户归属
        """
        from framework.common.ctx import get_tenant_id

        return get_tenant_id()

    @classmethod
    def require_tenant_id(cls, request: "Request") -> str:
        """解析租户标识，不存在则抛出异常

        Args:
            request: HTTP 请求对象

        Returns:
            租户 ID

        Raises:
            TenantResolveError: 无法解析租户标识
        """
        tenant_id = cls.resolve(request)
        if not tenant_id:
            raise TenantResolveError("无法解析租户标识，请在请求头中提供 X-Tenant-Id")
        return tenant_id
