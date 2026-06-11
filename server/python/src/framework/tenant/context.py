"""
租户上下文管理

提供请求级别的租户上下文存储。

注意：TenantContext 现在是 Context 的适配器，底层使用 Context 存储租户信息。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from framework.common.ctx import get_context
from framework.tenant.protocols import (
    TenantCacheConfig,
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
    cache: TenantCacheConfig | None = None

    @classmethod
    def from_model(
        cls,
        model: Any,
        database: TenantDatabaseConfig | None = None,
        storage: TenantStorageConfig | None = None,
        queue: TenantQueueConfig | None = None,
        pubsub: TenantPubSubConfig | None = None,
        cache: TenantCacheConfig | None = None,
    ) -> "SimpleTenant":
        """从 ORM 模型创建

        Args:
            model: Tenant ORM 模型实例
            database: 数据库配置（需在调用方从关联表加载）
            storage: 存储配置（需在调用方从关联表加载）
            queue: 队列配置（需在调用方从关联表加载）
            pubsub: 发布订阅配置（需在调用方从关联表加载）
            cache: 缓存配置（需在调用方从关联表加载）

        Returns:
            SimpleTenant: 简化的租户信息实例
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
            database=database,
            storage=storage,
            queue=queue,
            pubsub=pubsub,
            cache=cache,
        )


# 租户配置在 Context.extra 中的 key
_TENANT_CONFIG_KEY = "tenant_config"


class TenantContext:
    """租户上下文适配器

    所有租户信息存储在 Context 中，此类提供便捷的访问方法。
    """

    @staticmethod
    def get_current_tenant() -> SimpleTenant | None:
        """获取当前租户

        从 Context 重建 SimpleTenant 对象
        """
        ctx = get_context()
        if not ctx.tenant_id:
            return None

        # 从 Context.extra 读取租户配置
        tenant_config = ctx.extra.get(_TENANT_CONFIG_KEY, {})

        return SimpleTenant(
            id=ctx.tenant_id,
            name=ctx.tenant_name or "",
            code=ctx.tenant_code or "",
            status=tenant_config.get("status", "active"),
            expired_at=tenant_config.get("expired_at"),
            contact_name=tenant_config.get("contact_name"),
            contact_email=tenant_config.get("contact_email"),
            contact_phone=tenant_config.get("contact_phone"),
            database=tenant_config.get("database"),
            storage=tenant_config.get("storage"),
            cache=tenant_config.get("cache"),
            queue=tenant_config.get("queue"),
            pubsub=tenant_config.get("pubsub"),
        )

    @staticmethod
    def set_current_tenant(tenant: SimpleTenant | Any | None) -> None:
        """设置当前租户

        Args:
            tenant: 可以是 SimpleTenant 实例或 ORM 模型实例
        """
        if tenant is None:
            ctx = get_context()
            ctx.tenant_id = None
            ctx.tenant_name = None
            ctx.tenant_code = None
            ctx.extra.pop(_TENANT_CONFIG_KEY, None)
            return

        # 转换为 SimpleTenant
        if not isinstance(tenant, SimpleTenant):
            tenant = SimpleTenant.from_model(tenant)

        ctx = get_context()
        ctx.tenant_id = tenant.id
        ctx.tenant_name = tenant.name
        ctx.tenant_code = tenant.code

        # 租户配置存储到 extra
        tenant_config = {
            "status": tenant.status,
            "expired_at": tenant.expired_at,
            "contact_name": tenant.contact_name,
            "contact_email": tenant.contact_email,
            "contact_phone": tenant.contact_phone,
            "database": tenant.database,
            "storage": tenant.storage,
            "cache": tenant.cache,
            "queue": tenant.queue,
            "pubsub": tenant.pubsub,
        }
        ctx.extra[_TENANT_CONFIG_KEY] = tenant_config

    @staticmethod
    def clear() -> None:
        """清理租户上下文"""
        ctx = get_context()
        ctx.tenant_id = None
        ctx.tenant_name = None
        ctx.tenant_code = None
        ctx.extra.pop(_TENANT_CONFIG_KEY, None)

    @staticmethod
    def get_tenant_id() -> str | None:
        """获取当前租户 ID"""
        return get_context().tenant_id

    @staticmethod
    def get_tenant_code() -> str | None:
        """获取当前租户编码"""
        return get_context().tenant_code

    @staticmethod
    def get_tenant_name() -> str | None:
        """获取当前租户名称"""
        return get_context().tenant_name

    @staticmethod
    def is_set() -> bool:
        """检查是否设置了租户上下文"""
        return get_context().tenant_id is not None

    @staticmethod
    def get_database_config() -> TenantDatabaseConfig | None:
        """获取当前租户的数据库配置"""
        ctx = get_context()
        tenant_config = ctx.extra.get(_TENANT_CONFIG_KEY, {})
        return tenant_config.get("database")

    @staticmethod
    def get_storage_config() -> TenantStorageConfig | None:
        """获取当前租户的存储配置"""
        ctx = get_context()
        tenant_config = ctx.extra.get(_TENANT_CONFIG_KEY, {})
        return tenant_config.get("storage")

    @staticmethod
    def get_cache_config() -> TenantCacheConfig | None:
        """获取当前租户的缓存配置"""
        ctx = get_context()
        tenant_config = ctx.extra.get(_TENANT_CONFIG_KEY, {})
        return tenant_config.get("cache")

    @staticmethod
    def get_queue_config() -> TenantQueueConfig | None:
        """获取当前租户的队列配置"""
        ctx = get_context()
        tenant_config = ctx.extra.get(_TENANT_CONFIG_KEY, {})
        return tenant_config.get("queue")

    @staticmethod
    def get_pubsub_config() -> TenantPubSubConfig | None:
        """获取当前租户的发布订阅配置"""
        ctx = get_context()
        tenant_config = ctx.extra.get(_TENANT_CONFIG_KEY, {})
        return tenant_config.get("pubsub")

    @staticmethod
    def has_physical_database() -> bool:
        """检查当前租户是否配置了物理隔离数据库"""
        config = TenantContext.get_database_config()
        return config is not None and bool(config.database)

    @staticmethod
    def has_physical_storage() -> bool:
        """检查当前租户是否配置了物理隔离存储桶"""
        config = TenantContext.get_storage_config()
        return config is not None and bool(config.bucket)

    @staticmethod
    def has_physical_cache() -> bool:
        """检查当前租户是否配置了物理隔离缓存"""
        config = TenantContext.get_cache_config()
        return config is not None


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
