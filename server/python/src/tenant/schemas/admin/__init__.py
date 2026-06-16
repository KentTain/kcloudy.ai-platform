"""
Tenant 模块管理后台 Schemas
"""

from .module import (
    ModuleCreate,
    ModuleListResponse,
    ModuleMenuCreate,
    ModuleMenuListResponse,
    ModuleMenuUpdate,
    ModuleMenuTreeResponse,
    ModulePermissionCreate,
    ModulePermissionListResponse,
    ModulePermissionUpdate,
    ModulePermissionResponse,
    ModuleRoleCreate,
    ModuleRoleListResponse,
    ModuleRolePermissionUpdateRequest,
    ModuleRoleUpdate,
    ModuleRoleResponse,
    ModuleUpdate,
    ModuleResponse,
)
from .tenant_module import (
    AssignModuleRequest,
    TenantModuleListResponse,
    TenantModuleResponse,
)

__all__ = [
    # 模块
    "ModuleCreate",
    "ModuleUpdate",
    "ModuleResponse",
    "ModuleListResponse",
    # 模块菜单
    "ModuleMenuCreate",
    "ModuleMenuUpdate",
    "ModuleMenuTreeResponse",
    "ModuleMenuListResponse",
    # 模块权限
    "ModulePermissionCreate",
    "ModulePermissionUpdate",
    "ModulePermissionResponse",
    "ModulePermissionListResponse",
    # 模块角色
    "ModuleRoleCreate",
    "ModuleRoleUpdate",
    "ModuleRolePermissionUpdateRequest",
    "ModuleRoleResponse",
    "ModuleRoleListResponse",
    # 租户模块分配
    "AssignModuleRequest",
    "TenantModuleResponse",
    "TenantModuleListResponse",
]
