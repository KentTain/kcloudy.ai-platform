"""
管理后台租户 Schema
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from framework.schemas import BaseModel
from pydantic import Field

if TYPE_CHECKING:
    from tenant.models import Tenant
    from tenant.models.cache_config import CacheConfig
    from tenant.models.database_config import DatabaseConfig
    from tenant.models.pubsub_config import PubSubConfig
    from tenant.models.queue_config import QueueConfig
    from tenant.models.storage_config import StorageConfig

# ============== 请求 Schema ==============

class TenantCreate(BaseModel):
    """创建租户请求"""
    name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    code: str = Field(..., min_length=1, max_length=50, description="租户编码")
    contact_name: str | None = Field(None, max_length=100, description="联系人姓名")
    contact_email: str | None = Field(None, max_length=128, description="联系人邮箱")
    contact_phone: str | None = Field(None, max_length=20, description="联系人电话")
    expired_at: datetime | None = Field(None, description="过期时间")
    settings: dict[str, Any] | None = Field(None, description="扩展设置")
    # 资源配置关联
    db_config_id: str | None = Field(None, description="数据库配置ID")
    storage_config_id: str | None = Field(None, description="存储配置ID")
    cache_config_id: str | None = Field(None, description="缓存配置ID")
    queue_config_id: str | None = Field(None, description="队列配置ID")
    pubsub_config_id: str | None = Field(None, description="发布订阅配置ID")

class TenantUpdate(BaseModel):
    """更新租户请求"""
    name: str | None = Field(None, min_length=1, max_length=100, description="租户名称")
    contact_name: str | None = Field(None, max_length=100, description="联系人姓名")
    contact_email: str | None = Field(None, max_length=128, description="联系人邮箱")
    contact_phone: str | None = Field(None, max_length=20, description="联系人电话")
    expired_at: datetime | None = Field(None, description="过期时间")
    settings: dict[str, Any] | None = Field(None, description="扩展设置")

class AdminLoginRequest(BaseModel):
    """管理员登录请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=100, description="密码")

class ResourceValidateResponse(BaseModel):
    """资源验证响应"""
    valid: bool = Field(..., description="是否有效")
    message: str = Field(..., description="验证消息")

# ============== 响应 Schema ==============

class ResourceConfigReferenceResponse(BaseModel):
    """资源配置引用响应"""

    id: str = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")

    @classmethod
    def from_config(
        cls,
        config: DatabaseConfig | StorageConfig | CacheConfig | QueueConfig | PubSubConfig | None,
    ) -> ResourceConfigReferenceResponse | None:
        """从配置对象构建响应

        Args:
            config: 配置对象，包含 id 和 name 属性

        Returns:
            ResourceConfigReferenceResponse 或 None（当 config 为 None 时）
        """
        if config is None:
            return None
        return cls(id=config.id, name=config.name)

class TenantResponse(BaseModel):
    """租户响应"""
    id: str = Field(..., description="租户ID")
    name: str = Field(..., description="租户名称")
    code: str = Field(..., description="租户编码")
    status: str = Field(..., description="状态")
    contact_name: str | None = Field(None, description="联系人姓名")
    contact_email: str | None = Field(None, description="联系人邮箱")
    contact_phone: str | None = Field(None, description="联系人电话")
    expired_at: datetime | None = Field(None, description="过期时间")
    settings: dict[str, Any] = Field(default_factory=dict, description="扩展设置")
    # 资源配置关联
    db_config: ResourceConfigReferenceResponse | None = Field(None, description="数据库配置")
    storage_config: ResourceConfigReferenceResponse | None = Field(None, description="存储配置")
    cache_config: ResourceConfigReferenceResponse | None = Field(None, description="缓存配置")
    queue_config: ResourceConfigReferenceResponse | None = Field(None, description="队列配置")
    pubsub_config: ResourceConfigReferenceResponse | None = Field(None, description="发布订阅配置")
    # 时间
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    @classmethod
    def from_tenant(
        cls,
        tenant: Tenant,
        db_config: ResourceConfigReferenceResponse | None = None,
        storage_config: ResourceConfigReferenceResponse | None = None,
        cache_config: ResourceConfigReferenceResponse | None = None,
        queue_config: ResourceConfigReferenceResponse | None = None,
        pubsub_config: ResourceConfigReferenceResponse | None = None,
    ) -> TenantResponse:
        """从租户对象和资源配置构建响应

        Args:
            tenant: 租户对象
            db_config: 数据库配置引用
            storage_config: 存储配置引用
            cache_config: 缓存配置引用
            queue_config: 队列配置引用
            pubsub_config: 发布订阅配置引用

        Returns:
            TenantResponse
        """
        return cls(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
            status=tenant.status,
            contact_name=tenant.contact_name,
            contact_email=tenant.contact_email,
            contact_phone=tenant.contact_phone,
            expired_at=tenant.expired_at,
            settings=tenant.settings or {},
            db_config=db_config,
            storage_config=storage_config,
            cache_config=cache_config,
            queue_config=queue_config,
            pubsub_config=pubsub_config,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )

class TenantListStats(BaseModel):
    """租户列表统计"""

    total_count: int = Field(..., description="租户总数")
    inactive_count: int = Field(..., description="未激活租户数")
    expired_count: int = Field(..., description="已过期租户数")


class TenantStatsResponse(BaseModel):
    """租户统计响应"""
    tenant_id: str = Field(..., description="租户ID")
    user_count: int = Field(0, description="用户数")
    storage_usage: int = Field(0, description="存储用量（字节）")
    active_users: int = Field(0, description="活跃用户数")

class AdminLoginResponse(BaseModel):
    """管理员登录响应"""
    token: str = Field(..., description="访问令牌")
    username: str = Field(..., description="用户名")
    is_default: bool = Field(..., description="是否默认管理员")

class AdminInfoResponse(BaseModel):
    """管理员信息响应"""
    id: str = Field(..., description="管理员ID")
    username: str = Field(..., description="用户名")
    is_default: bool = Field(..., description="是否默认管理员")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")

# ============== 资源绑定 Schema ==============

class ResourceBindingRequest(BaseModel):
    """资源绑定请求"""

    db_config_id: str | None = Field(None, description="数据库配置ID")
    storage_config_id: str | None = Field(None, description="存储配置ID")
    cache_config_id: str | None = Field(None, description="缓存配置ID")
    queue_config_id: str | None = Field(None, description="队列配置ID")
    pubsub_config_id: str | None = Field(None, description="发布订阅配置ID")

class ResourceBindingResponse(BaseModel):
    """资源绑定响应"""

    tenant_id: str = Field(..., description="租户ID")
    db_config: ResourceConfigReferenceResponse | None = Field(None, description="数据库配置")
    storage_config: ResourceConfigReferenceResponse | None = Field(None, description="存储配置")
    cache_config: ResourceConfigReferenceResponse | None = Field(None, description="缓存配置")
    queue_config: ResourceConfigReferenceResponse | None = Field(None, description="队列配置")
    pubsub_config: ResourceConfigReferenceResponse | None = Field(None, description="发布订阅配置")
