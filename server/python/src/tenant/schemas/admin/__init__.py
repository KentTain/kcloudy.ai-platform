"""
Tenant 模块管理后台 Schemas
"""

from .module import (
    ModuleCreate,
    ModulePaginatedListResponse,
    ModuleMenuCreate,
    ModuleMenuListResponse,
    ModuleMenuUpdate,
    ModuleMenuTreeResponse,
    ModulePermissionCreate,
    ModulePermissionPaginatedListResponse,
    ModulePermissionUpdate,
    ModulePermissionResponse,
    ModuleRoleCreate,
    ModuleRolePaginatedListResponse,
    ModuleRolePermissionUpdateRequest,
    ModuleRoleUpdate,
    ModuleRoleResponse,
    ModuleUpdate,
    ModuleResponse,
)
from .tenant_module import (
    AssignModuleRequest,
    TenantModulePaginatedListResponse,
    TenantModuleResponse,
)

__all__ = [
    # 模块
    "ModuleCreate",
    "ModuleUpdate",
    "ModuleResponse",
    "ModulePaginatedListResponse",
    # 模块菜单
    "ModuleMenuCreate",
    "ModuleMenuUpdate",
    "ModuleMenuTreeResponse",
    "ModuleMenuListResponse",
    # 模块权限
    "ModulePermissionCreate",
    "ModulePermissionUpdate",
    "ModulePermissionResponse",
    "ModulePermissionPaginatedListResponse",
    # 模块角色
    "ModuleRoleCreate",
    "ModuleRoleUpdate",
    "ModuleRolePermissionUpdateRequest",
    "ModuleRoleResponse",
    "ModuleRolePaginatedListResponse",
    # 租户模块分配
    "AssignModuleRequest",
    "TenantModuleResponse",
    "TenantModulePaginatedListResponse",
]
