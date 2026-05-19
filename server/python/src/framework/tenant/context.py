"""
租户上下文管理

提供请求级别的租户上下文存储。
"""

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framework.tenant.models import Tenant


_tenant_context: ContextVar["Tenant | None"] = ContextVar("tenant_context", default=None)


class TenantContext:
    """租户上下文管理类"""

    @staticmethod
    def get_current_tenant() -> "Tenant | None":
        """获取当前租户"""
        return _tenant_context.get()

    @staticmethod
    def set_current_tenant(tenant: "Tenant | None") -> None:
        """设置当前租户"""
        _tenant_context.set(tenant)

    @staticmethod
    def clear() -> None:
        """清理租户上下文"""
        _tenant_context.set(None)

    @staticmethod
    def get_tenant_id() -> str | None:
        """获取当前租户 ID"""
        tenant = _tenant_context.get()
        return tenant.id if tenant else None


def get_current_tenant() -> "Tenant | None":
    """获取当前租户"""
    return TenantContext.get_current_tenant()


def set_current_tenant(tenant: "Tenant | None") -> None:
    """设置当前租户"""
    TenantContext.set_current_tenant(tenant)


def clear_tenant_context() -> None:
    """清理租户上下文"""
    TenantContext.clear()


def get_tenant_id() -> str | None:
    """获取当前租户 ID"""
    return TenantContext.get_tenant_id()
