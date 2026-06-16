"""
Tenant 模块 Schemas
"""

from .admin.resource_config import (
    CacheConfigCreate,
    CachePropertyPaginatedListResponse,
    CachePropertyResponse,
    CacheConfigUpdate,
    ConnectionTestResult,
    DatabaseConfigCreate,
    DatabasePropertyPaginatedListResponse,
    DatabasePropertyResponse,
    DatabaseConfigUpdate,
    PubSubConfigCreate,
    PubSubPropertyPaginatedListResponse,
    PubSubPropertyResponse,
    PubSubConfigUpdate,
    QueueConfigCreate,
    QueuePropertyPaginatedListResponse,
    QueuePropertyResponse,
    QueueConfigUpdate,
    ResourceQuery,
    ResourcePaginatedQuery,
    StorageConfigCreate,
    StoragePropertyPaginatedListResponse,
    StoragePropertyResponse,
    StorageConfigUpdate,
)
from .admin.tenant import (
    ResourceBindingRequest,
    ResourceBindingResponse,
    TenantCreate,
    TenantUpdate,
    AdminLoginRequest,
    ResourceValidateResponse,
    TenantResponse,
    TenantPaginatedListResponse,
    TenantStatsResponse,
    AdminLoginResponse,
    AdminInfoResponse,
)
from .console.tenant import (
    UserTenantResponse,
    CurrentTenantResponse,
    SwitchTenantResponse,
)

__all__ = [
    # 资源配置 - 数据库
    "DatabaseConfigCreate",
    "DatabaseConfigUpdate",
    "DatabasePropertyResponse",
    "DatabasePropertyPaginatedListResponse",
    # 资源配置 - 存储
    "StorageConfigCreate",
    "StorageConfigUpdate",
    "StoragePropertyResponse",
    "StoragePropertyPaginatedListResponse",
    # 资源配置 - 缓存
    "CacheConfigCreate",
    "CacheConfigUpdate",
    "CachePropertyResponse",
    "CachePropertyPaginatedListResponse",
    # 资源配置 - 队列
    "QueueConfigCreate",
    "QueueConfigUpdate",
    "QueuePropertyResponse",
    "QueuePropertyPaginatedListResponse",
    # 资源配置 - 发布订阅
    "PubSubConfigCreate",
    "PubSubConfigUpdate",
    "PubSubPropertyResponse",
    "PubSubPropertyPaginatedListResponse",
    # 资源配置 - 通用
    "ResourceQuery",
    "ResourcePaginatedQuery",
    "ConnectionTestResult",
    # 资源绑定
    "ResourceBindingRequest",
    "ResourceBindingResponse",
    # 请求
    "TenantCreate",
    "TenantUpdate",
    "AdminLoginRequest",
    # 响应
    "ResourceValidateResponse",
    "TenantResponse",
    "TenantPaginatedListResponse",
    "TenantStatsResponse",
    "AdminLoginResponse",
    "AdminInfoResponse",
    # 用户端
    "UserTenantResponse",
    "CurrentTenantResponse",
    "SwitchTenantResponse",
]
