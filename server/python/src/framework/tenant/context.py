"""
租户上下文管理

提供请求级别的租户上下文存储。
"""

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    pass


class TenantInfo(Protocol):
    """租户信息协议"""

    @property
    def id(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def code(self) -> str: ...

    @property
    def status(self) -> str: ...


@dataclass
class SimpleTenant:
    """简化的租户信息，用于上下文存储"""

    id: str
    name: str
    code: str
    status: str = "active"

    @classmethod
    def from_model(cls, model: Any) -> "SimpleTenant":
        """从 ORM 模型创建"""
        return cls(
            id=model.id,
            name=model.name,
            code=model.code,
            status=model.status,
        )


_tenant_context: ContextVar[SimpleTenant | None] = ContextVar(
    "tenant_context", default=None
)


class TenantContext:
    """租户上下文管理类"""

    @staticmethod
    def get_current_tenant() -> SimpleTenant | None:
        """获取当前租户"""
        return _tenant_context.get()

    @staticmethod
    def set_current_tenant(tenant: SimpleTenant | Any | None) -> None:
        """设置当前租户

        Args:
            tenant: 可以是 SimpleTenant 实例或 ORM 模型实例
        """
        if tenant is None:
            _tenant_context.set(None)
        elif isinstance(tenant, SimpleTenant):
            _tenant_context.set(tenant)
        else:
            _tenant_context.set(SimpleTenant.from_model(tenant))

    @staticmethod
    def clear() -> None:
        """清理租户上下文"""
        _tenant_context.set(None)

    @staticmethod
    def get_tenant_id() -> str | None:
        """获取当前租户 ID"""
        tenant = _tenant_context.get()
        return tenant.id if tenant else None

    @staticmethod
    def get_tenant_code() -> str | None:
        """获取当前租户编码"""
        tenant = _tenant_context.get()
        return tenant.code if tenant else None

    @staticmethod
    def get_tenant_name() -> str | None:
        """获取当前租户名称"""
        tenant = _tenant_context.get()
        return tenant.name if tenant else None

    @staticmethod
    def is_set() -> bool:
        """检查是否设置了租户上下文"""
        return _tenant_context.get() is not None


def get_current_tenant() -> SimpleTenant | None:
    """获取当前租户"""
    return TenantContext.get_current_tenant()


def set_current_tenant(tenant: SimpleTenant | Any | None) -> None:
    """设置当前租户"""
    TenantContext.set_current_tenant(tenant)


def clear_tenant_context() -> None:
    """清理租户上下文"""
    TenantContext.clear()


def get_tenant_id() -> str | None:
    """获取当前租户 ID"""
    return TenantContext.get_tenant_id()


def get_tenant_code() -> str | None:
    """获取当前租户编码"""
    return TenantContext.get_tenant_code()


def get_tenant_name() -> str | None:
    """获取当前租户名称"""
    return TenantContext.get_tenant_name()
