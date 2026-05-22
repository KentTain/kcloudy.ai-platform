"""
管理后台租户 Schema
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============== 资源配置 Schema ==============

class DatabaseConfigRequest(BaseModel):
    """数据库配置请求"""
    db_type: str | None = Field(None, max_length=20, description="数据库类型")
    db_host: str | None = Field(None, max_length=255, description="数据库主机")
    db_port: int | None = Field(None, description="数据库端口")
    db_name: str | None = Field(None, max_length=100, description="数据库名称")
    db_username: str | None = Field(None, max_length=100, description="数据库用户名")
    db_password: str | None = Field(None, max_length=255, description="数据库密码")


class StorageConfigRequest(BaseModel):
    """存储配置请求"""
    storage_type: str | None = Field(None, max_length=20, description="存储类型")
    storage_bucket: str | None = Field(None, max_length=100, description="存储桶名称")


class CacheConfigRequest(BaseModel):
    """缓存配置请求"""
    cache_db: int | None = Field(None, ge=0, le=15, description="Redis DB 编号 (0-15)")


class DatabaseConfigVo(BaseModel):
    """数据库配置响应"""
    db_type: str | None = Field(None, description="数据库类型")
    db_host: str | None = Field(None, description="数据库主机")
    db_port: int | None = Field(None, description="数据库端口")
    db_name: str | None = Field(None, description="数据库名称")
    db_username: str | None = Field(None, description="数据库用户名")
    # 密码不返回


class StorageConfigVo(BaseModel):
    """存储配置响应"""
    storage_type: str | None = Field(None, description="存储类型")
    storage_bucket: str | None = Field(None, description="存储桶名称")


class CacheConfigVo(BaseModel):
    """缓存配置响应"""
    cache_db: int | None = Field(None, description="Redis DB 编号")


# ============== 请求 Schema ==============

class TenantCreateRequest(BaseModel):
    """创建租户请求"""
    name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    code: str = Field(..., min_length=1, max_length=50, description="租户编码")
    contact_name: str | None = Field(None, max_length=100, description="联系人姓名")
    contact_email: str | None = Field(None, max_length=128, description="联系人邮箱")
    contact_phone: str | None = Field(None, max_length=20, description="联系人电话")
    expired_at: datetime | None = Field(None, description="过期时间")
    settings: dict[str, Any] | None = Field(None, description="扩展设置")
    # 资源配置
    database: DatabaseConfigRequest | None = Field(None, description="数据库配置")
    storage: StorageConfigRequest | None = Field(None, description="存储配置")
    cache: CacheConfigRequest | None = Field(None, description="缓存配置")


class TenantUpdateRequest(BaseModel):
    """更新租户请求"""
    name: str | None = Field(None, min_length=1, max_length=100, description="租户名称")
    contact_name: str | None = Field(None, max_length=100, description="联系人姓名")
    contact_email: str | None = Field(None, max_length=128, description="联系人邮箱")
    contact_phone: str | None = Field(None, max_length=20, description="联系人电话")
    expired_at: datetime | None = Field(None, description="过期时间")
    settings: dict[str, Any] | None = Field(None, description="扩展设置")
    # 资源配置
    database: DatabaseConfigRequest | None = Field(None, description="数据库配置")
    storage: StorageConfigRequest | None = Field(None, description="存储配置")
    cache: CacheConfigRequest | None = Field(None, description="缓存配置")


class AdminLoginRequest(BaseModel):
    """管理员登录请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=100, description="密码")


class ResourceValidateVo(BaseModel):
    """资源验证响应"""
    valid: bool = Field(..., description="是否有效")
    message: str = Field(..., description="验证消息")


# ============== 响应 Schema ==============

class TenantVo(BaseModel):
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
    # 资源配置
    database: DatabaseConfigVo | None = Field(None, description="数据库配置")
    storage: StorageConfigVo | None = Field(None, description="存储配置")
    cache: CacheConfigVo | None = Field(None, description="缓存配置")
    # 时间
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class TenantListVo(BaseModel):
    """租户列表响应"""
    items: list[TenantVo] = Field(default_factory=list, description="租户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


class TenantStatsVo(BaseModel):
    """租户统计响应"""
    tenant_id: str = Field(..., description="租户ID")
    user_count: int = Field(0, description="用户数")
    storage_usage: int = Field(0, description="存储用量（字节）")
    active_users: int = Field(0, description="活跃用户数")


class AdminLoginVo(BaseModel):
    """管理员登录响应"""
    token: str = Field(..., description="访问令牌")
    username: str = Field(..., description="用户名")
    is_default: bool = Field(..., description="是否默认管理员")


class AdminInfoVo(BaseModel):
    """管理员信息响应"""
    id: str = Field(..., description="管理员ID")
    username: str = Field(..., description="用户名")
    is_default: bool = Field(..., description="是否默认管理员")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
