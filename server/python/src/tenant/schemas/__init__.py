"""
Tenant 模块 Schemas
"""

from .admin.resource_config import (
    CacheConfigCreate,
    CacheConfigUpdate,
    CachePropertyPaginatedListResponse,
    CachePropertyResponse,
    ConnectionTestResult,
    DatabaseConfigCreate,
    DatabaseConfigUpdate,
    DatabasePropertyPaginatedListResponse,
    DatabasePropertyResponse,
    PubSubConfigCreate,
    PubSubConfigUpdate,
    PubSubPropertyPaginatedListResponse,
    PubSubPropertyResponse,
    QueueConfigCreate,
    QueueConfigUpdate,
    QueuePropertyPaginatedListResponse,
    QueuePropertyResponse,
    ResourcePaginatedQuery,
    ResourceQuery,
    StorageConfigCreate,
    StorageConfigUpdate,
    StoragePropertyPaginatedListResponse,
    StoragePropertyResponse,
)
from .admin.tenant import (
    AdminInfoResponse,
    AdminLoginRequest,
    AdminLoginResponse,
    ResourceBindingRequest,
    ResourceBindingResponse,
    ResourceValidateResponse,
    TenantCreate,
    TenantResponse,
    TenantStatsResponse,
    TenantUpdate,
)
from .console.tenant import (
    CurrentTenantResponse,
    SwitchTenantResponse,
    UserTenantResponse,
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
    "TenantStatsResponse",
    "AdminLoginResponse",
    "AdminInfoResponse",
    # 用户端
    "UserTenantResponse",
    "CurrentTenantResponse",
    "SwitchTenantResponse",
]
