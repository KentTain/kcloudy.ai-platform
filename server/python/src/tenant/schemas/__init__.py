"""
Tenant 模块 Schemas
"""

from .admin.resource_config import (
    CacheConfigCreate,
    CachePropertyListResponse,
    CachePropertyResponse,
    CacheConfigUpdate,
    ConnectionTestResult,
    DatabaseConfigCreate,
    DatabasePropertyListResponse,
    DatabasePropertyResponse,
    DatabaseConfigUpdate,
    PubSubConfigCreate,
    PubSubPropertyListResponse,
    PubSubPropertyResponse,
    PubSubConfigUpdate,
    QueueConfigCreate,
    QueuePropertyListResponse,
    QueuePropertyResponse,
    QueueConfigUpdate,
    ResourceQuery,
    StorageConfigCreate,
    StoragePropertyListResponse,
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
    TenantListResponse,
    TenantStatsResponse,
    AdminLoginResponse,
    AdminInfoResponse,
)
from .console.tenant import (
    UserTenantVo,
    CurrentTenantVo,
    SwitchTenantVo,
)

__all__ = [
    # 资源配置 - 数据库
    "DatabaseConfigCreate",
    "DatabaseConfigUpdate",
    "DatabasePropertyResponse",
    "DatabasePropertyListResponse",
    # 资源配置 - 存储
    "StorageConfigCreate",
    "StorageConfigUpdate",
    "StoragePropertyResponse",
    "StoragePropertyListResponse",
    # 资源配置 - 缓存
    "CacheConfigCreate",
    "CacheConfigUpdate",
    "CachePropertyResponse",
    "CachePropertyListResponse",
    # 资源配置 - 队列
    "QueueConfigCreate",
    "QueueConfigUpdate",
    "QueuePropertyResponse",
    "QueuePropertyListResponse",
    # 资源配置 - 发布订阅
    "PubSubConfigCreate",
    "PubSubConfigUpdate",
    "PubSubPropertyResponse",
    "PubSubPropertyListResponse",
    # 资源配置 - 通用
    "ResourceQuery",
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
    "TenantListResponse",
    "TenantStatsResponse",
    "AdminLoginResponse",
    "AdminInfoResponse",
    # 用户端
    "UserTenantVo",
    "CurrentTenantVo",
    "SwitchTenantVo",
]
