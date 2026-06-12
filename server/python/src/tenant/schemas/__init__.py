"""
Tenant 模块 Schemas
"""

from .admin.resource_config import (
    CacheConfigCreateRequest,
    CacheConfigListResponse,
    CacheConfigResponse,
    CacheConfigUpdateRequest,
    ConnectionTestResult,
    DatabaseConfigCreateRequest,
    DatabaseConfigListResponse,
    DatabaseConfigResponse,
    DatabaseConfigUpdateRequest,
    PubSubConfigCreateRequest,
    PubSubConfigListResponse,
    PubSubConfigResponse,
    PubSubConfigUpdateRequest,
    QueueConfigCreateRequest,
    QueueConfigListResponse,
    QueueConfigResponse,
    QueueConfigUpdateRequest,
    ResourceListQuery,
    StorageConfigCreateRequest,
    StorageConfigListResponse,
    StorageConfigResponse,
    StorageConfigUpdateRequest,
)
from .admin.tenant import (
    ResourceBindingRequest,
    ResourceBindingResponse,
    TenantCreateRequest,
    TenantUpdateRequest,
    AdminLoginRequest,
    ResourceValidateVo,
    TenantVo,
    TenantListVo,
    TenantStatsVo,
    AdminLoginVo,
    AdminInfoVo,
)
from .console.tenant import (
    UserTenantVo,
    CurrentTenantVo,
    SwitchTenantVo,
)

__all__ = [
    # 资源配置 - 数据库
    "DatabaseConfigCreateRequest",
    "DatabaseConfigUpdateRequest",
    "DatabaseConfigResponse",
    "DatabaseConfigListResponse",
    # 资源配置 - 存储
    "StorageConfigCreateRequest",
    "StorageConfigUpdateRequest",
    "StorageConfigResponse",
    "StorageConfigListResponse",
    # 资源配置 - 缓存
    "CacheConfigCreateRequest",
    "CacheConfigUpdateRequest",
    "CacheConfigResponse",
    "CacheConfigListResponse",
    # 资源配置 - 队列
    "QueueConfigCreateRequest",
    "QueueConfigUpdateRequest",
    "QueueConfigResponse",
    "QueueConfigListResponse",
    # 资源配置 - 发布订阅
    "PubSubConfigCreateRequest",
    "PubSubConfigUpdateRequest",
    "PubSubConfigResponse",
    "PubSubConfigListResponse",
    # 资源配置 - 通用
    "ResourceListQuery",
    "ConnectionTestResult",
    # 资源绑定
    "ResourceBindingRequest",
    "ResourceBindingResponse",
    # 请求
    "TenantCreateRequest",
    "TenantUpdateRequest",
    "AdminLoginRequest",
    # 响应
    "ResourceValidateVo",
    "TenantVo",
    "TenantListVo",
    "TenantStatsVo",
    "AdminLoginVo",
    "AdminInfoVo",
    # 用户端
    "UserTenantVo",
    "CurrentTenantVo",
    "SwitchTenantVo",
]
