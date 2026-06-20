"""
Tenant 模块服务层
"""

from .cache_config_service import CacheConfigService, cache_config_service
from .database_config_service import DatabaseConfigService, database_config_service
from .module_menu_permission_service import ModuleMenuPermissionService
from .module_menu_service import ModuleMenuService
from .module_permission_service import ModulePermissionService
from .module_role_service import ModuleRoleService
from .module_service import ModuleService
from .pubsub_config_service import PubSubConfigService, pubsub_config_service
from .queue_config_service import QueueConfigService, queue_config_service
from .storage_config_service import StorageConfigService, storage_config_service
from .tenant_module_service import TenantModuleService, tenant_module_service
from .tenant_provider_impl import TenantProviderImpl, tenant_provider_impl
from .tenant_service import TenantService, tenant_service

__all__ = [
    "TenantService",
    "tenant_service",
    "TenantProviderImpl",
    "tenant_provider_impl",
    # 资源配置服务
    "DatabaseConfigService",
    "database_config_service",
    "StorageConfigService",
    "storage_config_service",
    "CacheConfigService",
    "cache_config_service",
    "QueueConfigService",
    "queue_config_service",
    "PubSubConfigService",
    "pubsub_config_service",
    # 模块定义层服务
    "ModuleService",
    "ModuleMenuService",
    "ModuleMenuPermissionService",
    "ModulePermissionService",
    "ModuleRoleService",
    # 租户模块分配服务
    "TenantModuleService",
    "tenant_module_service",
]
