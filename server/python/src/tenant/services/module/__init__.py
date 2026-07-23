"""
模块定义服务子包

包含模块定义服务：ModuleService、ModuleMenuService、ModulePermissionService 等
"""

from .module_menu_permission_service import (
    ModuleMenuPermissionService,
    module_menu_permission_service,
)
from .module_menu_service import ModuleMenuService, module_menu_service
from .module_permission_service import (
    ModulePermissionService,
    module_permission_service,
)
from .module_role_service import ModuleRoleService, module_role_service
from .module_service import ModuleService, module_service
from .module_sync_provider import (
    ModuleDefinitionSyncProviderImpl,
    module_definition_sync_provider_impl,
)

__all__ = [
    "ModuleService",
    "module_service",
    "ModuleMenuService",
    "module_menu_service",
    "ModuleMenuPermissionService",
    "module_menu_permission_service",
    "ModulePermissionService",
    "module_permission_service",
    "ModuleRoleService",
    "module_role_service",
    "ModuleDefinitionSyncProviderImpl",
    "module_definition_sync_provider_impl",
]
