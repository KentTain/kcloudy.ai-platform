"""
Tenant 模块 Schemas
"""

from .admin.tenant import (
    DatabaseConfigRequest,
    DatabaseConfigVo,
    StorageConfigRequest,
    StorageConfigVo,
    CacheConfigRequest,
    CacheConfigVo,
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
    # 资源配置
    "DatabaseConfigRequest",
    "DatabaseConfigVo",
    "StorageConfigRequest",
    "StorageConfigVo",
    "CacheConfigRequest",
    "CacheConfigVo",
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
