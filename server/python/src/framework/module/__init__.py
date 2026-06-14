"""
模块系统

提供模块声明、扫描、加载和注册功能。
"""

from framework.module.definition import (
    MenuDef,
    ModuleDefinition,
    PermissionDef,
    RoleDef,
)
from framework.module.descriptor import ModuleDescriptor
from framework.module.registry import ModuleRegistry, get_registry
from framework.module.loader import (
    CyclicDependencyError,
    ModuleLoadError,
    discover_modules,
    filter_modules,
    load_modules,
    resolve_dependencies,
)
from framework.module.sync_service import ModuleDefinitionSyncService

__all__ = [
    # Definition
    "MenuDef",
    "ModuleDefinition",
    "PermissionDef",
    "RoleDef",
    # Descriptor
    "ModuleDescriptor",
    # Registry
    "ModuleRegistry",
    "get_registry",
    # Loader
    "CyclicDependencyError",
    "ModuleLoadError",
    "discover_modules",
    "filter_modules",
    "load_modules",
    "resolve_dependencies",
    # Sync Service
    "ModuleDefinitionSyncService",
]
