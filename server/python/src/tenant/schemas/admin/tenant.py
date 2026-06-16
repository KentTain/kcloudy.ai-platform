"""
管理后台租户 Schema
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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


class TenantPaginatedListResponse(BaseModel):
    """租户分页列表响应"""
    items: list[TenantResponse] = Field(default_factory=list, description="租户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


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
