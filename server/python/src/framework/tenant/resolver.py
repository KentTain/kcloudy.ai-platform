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
    2. 用户信息中的 tenant_id
    3. 用户默认租户
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

        # 优先级 2: 从用户信息获取
        tenant_id = cls._resolve_from_user(request)
        if tenant_id:
            return tenant_id

        return None

    @classmethod
    def _resolve_from_header(cls, request: "Request") -> str | None:
        """从请求头解析租户 ID"""
        return request.headers.get(cls.HEADER_TENANT_ID)

    @classmethod
    def _resolve_from_user(cls, request: "Request") -> str | None:
        """从用户信息解析租户 ID

        用户信息可能来自：
        1. request.state.user (认证中间件设置)
        2. request.state.context (通用上下文)
        """
        # 从 request.state.user 获取
        user = getattr(request.state, "user", None)
        if user:
            # 支持对象属性
            if hasattr(user, "tenant_id"):
                return user.tenant_id
            # 支持字典类型
            if isinstance(user, dict) and "tenant_id" in user:
                return user["tenant_id"]

        # 从 request.state.context 获取
        context = getattr(request.state, "context", None)
        if context:
            if hasattr(context, "tenant_id"):
                return context.tenant_id

        return None

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
