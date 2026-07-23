"""
Tenant 模块数据模型

包含租户管理相关的所有模型。
所有模型归属于 tenant PostgreSQL schema。
"""

from framework.database import create_base_model, create_module_base

# 创建 Tenant 模块的 Base 和 BaseModel
Base = create_module_base("tenant")
BaseModel = create_base_model(Base)

# 导入枚举（保留在根目录）
from .enums import TenantStatus, PluginInstallType

# 导入模型（从子目录）
from .tenant import (
    Tenant,
    TenantAdmin,
    TenantBusinessConfig,
    TenantConfig,
    TenantModule,
)
from .resource import (
    CacheConfig,
    DatabaseConfig,
    PubSubConfig,
    QueueConfig,
    StorageConfig,
)
from .module import (
    Module,
    ModuleMenu,
    ModuleMenuPermission,
    ModulePermission,
    ModuleRole,
    ModuleRolePermission,
)
from .plugin import (
    TenantPluginDefinition,
    TenantPluginInstallation,
    TenantPluginMarketplace,
    TenantPluginPackage,
)

__all__ = [
    "Base",
    "BaseModel",
    # 枚举
    "TenantStatus",
    "PluginInstallType",
    # 租户相关
    "Tenant",
    "TenantConfig",
    "TenantAdmin",
    "TenantBusinessConfig",
    "TenantModule",
    # 资源配置
    "DatabaseConfig",
    "StorageConfig",
    "CacheConfig",
    "QueueConfig",
    "PubSubConfig",
    # 模块定义
    "Module",
    "ModuleMenu",
    "ModuleMenuPermission",
    "ModulePermission",
    "ModuleRole",
    "ModuleRolePermission",
    # 插件管理
    "TenantPluginDefinition",
    "TenantPluginInstallation",
    "TenantPluginMarketplace",
    "TenantPluginPackage",
]
