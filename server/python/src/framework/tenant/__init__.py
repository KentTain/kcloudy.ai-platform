"""
租户模块

提供多租户模型设计和实现。
"""

from framework.tenant.cache import TenantCache
from framework.tenant.context import (
    SimpleTenant,
    TenantContext,
    clear_tenant_context,
    get_current_tenant,
    get_tenant_code,
    get_tenant_id,
    get_tenant_name,
    set_current_tenant,
)
from framework.tenant.enums import (
    CacheType,
    DatabaseType,
    NoSqlType,
    PubSubType,
    QueueType,
    StorageType,
)
from framework.tenant.exceptions import (
    TenantAccessDeniedError,
    TenantAdminAuthError,
    TenantAdminNotFoundError,
    TenantError,
    TenantExpiredError,
    TenantInactiveError,
    TenantNotFoundError,
    TenantNotSetError,
    TenantResolveError,
)
from framework.tenant.middleware import TenantMiddleware
from framework.tenant.tenant_protocols import (
    TenantCacheConfig,
    TenantDatabaseConfig,
    TenantInfo,
    TenantProvider,
    TenantPubSubConfig,
    TenantQueueConfig,
    TenantStorageConfig,
    get_tenant_provider,
    register_tenant_provider,
)
from framework.tenant.resolver import TenantResolver
from framework.tenant.sync_protocols import (
    ModuleAutoAssigner,
    ModuleDefinitionSyncProvider,
    get_module_auto_assigner,
    get_module_definition_sync_provider,
    register_module_auto_assigner,
    register_module_definition_sync_provider,
)

__all__ = [
    # Cache
    "TenantCache",
    # Context
    "SimpleTenant",
    "TenantContext",
    "clear_tenant_context",
    "get_current_tenant",
    "get_tenant_code",
    "get_tenant_id",
    "get_tenant_name",
    "set_current_tenant",
    # Enums
    "CacheType",
    "DatabaseType",
    "NoSqlType",
    "PubSubType",
    "QueueType",
    "StorageType",
    # Exceptions
    "TenantAccessDeniedError",
    "TenantAdminAuthError",
    "TenantAdminNotFoundError",
    "TenantError",
    "TenantExpiredError",
    "TenantInactiveError",
    "TenantNotFoundError",
    "TenantNotSetError",
    "TenantResolveError",
    # Middleware
    "TenantMiddleware",
    # Protocols
    "TenantCacheConfig",
    "TenantDatabaseConfig",
    "TenantInfo",
    "TenantProvider",
    "TenantPubSubConfig",
    "TenantQueueConfig",
    "TenantStorageConfig",
    "get_tenant_provider",
    "register_tenant_provider",
    # Resolver
    "TenantResolver",
    # Sync Protocols
    "ModuleAutoAssigner",
    "ModuleDefinitionSyncProvider",
    "get_module_auto_assigner",
    "register_module_auto_assigner",
    "get_module_definition_sync_provider",
    "register_module_definition_sync_provider",
]
