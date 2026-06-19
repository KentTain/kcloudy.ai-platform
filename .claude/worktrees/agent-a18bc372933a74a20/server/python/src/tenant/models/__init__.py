"""
Tenant 模块数据模型

包含租户管理相关的所有模型。
所有模型归属于 tenant PostgreSQL schema。
"""

from framework.database import create_module_base, create_base_model

# 创建 Tenant 模块的 Base 和 BaseModel
Base = create_module_base("tenant")
BaseModel = create_base_model(Base)

# 导入模型（必须在 Base 和 BaseModel 定义之后）
from .cache_config import CacheConfig
from .database_config import DatabaseConfig
from .enums import TenantStatus
from .module import Module
from .module_menu import ModuleMenu
from .module_permission import ModulePermission
from .module_role import ModuleRole
from .module_role_permission import ModuleRolePermission
from .pubsub_config import PubSubConfig
from .queue_config import QueueConfig
from .storage_config import StorageConfig
from .tenant import Tenant
from .tenant_admin import TenantAdmin
from .tenant_business_config import TenantBusinessConfig
from .tenant_config import TenantConfig
from .tenant_module import TenantModule

__all__ = [
    "Base",
    "BaseModel",
    # 枚举
    "TenantStatus",
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
    "ModulePermission",
    "ModuleRole",
    "ModuleRolePermission",
]
