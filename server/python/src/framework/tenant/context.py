"""
租户上下文管理

提供请求级别的租户上下文存储。
"""

from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from framework.tenant.protocols import (
    TenantDatabaseConfig,
    TenantInfo,
    TenantQueueConfig,
    TenantPubSubConfig,
    TenantStorageConfig,
)


@dataclass
class SimpleTenant:
    """
    简化的租户信息，用于上下文存储

    实现 TenantInfo Protocol。
    """

    # 基础信息
    id: str
    name: str
    code: str
    status: str = "active"

    # 时间信息（可选）
    expired_at: datetime | None = None

    # 联系人信息（可选）
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None

    # 资源配置（可选，支持租户级隔离）
    database: TenantDatabaseConfig | None = None
    storage: TenantStorageConfig | None = None
    queue: TenantQueueConfig | None = None
    pubsub: TenantPubSubConfig | None = None

    @classmethod
    def from_model(cls, model: Any) -> "SimpleTenant":
        """从 ORM 模型创建

        注意：当前仅提取基础信息和联系人字段。
        资源配置（database/storage/queue/pubsub）需要在业务层单独设置，
        或通过扩展 ORM 模型添加资源配置字段后在此处映射。
        """
        return cls(
            id=model.id,
            name=model.name,
            code=model.code,
            status=model.status,
            expired_at=getattr(model, "expired_at", None),
            contact_name=getattr(model, "contact_name", None),
            contact_email=getattr(model, "contact_email", None),
            contact_phone=getattr(model, "contact_phone", None),
            # 资源配置：当前 ORM 模型暂未支持，待扩展
            # database=_extract_database_config(model),
            # storage=_extract_storage_config(model),
            # queue=_extract_queue_config(model),
            # pubsub=_extract_pubsub_config(model),
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
