"""
Tenant 模块管理后台 Schemas
"""

from .module import (
    ModuleCreateRequest,
    ModuleListVo,
    ModuleMenuCreateRequest,
    ModuleMenuListVo,
    ModuleMenuUpdateRequest,
    ModuleMenuVo,
    ModulePermissionCreateRequest,
    ModulePermissionListVo,
    ModulePermissionUpdateRequest,
    ModulePermissionVo,
    ModuleRoleCreateRequest,
    ModuleRoleListVo,
    ModuleRolePermissionUpdateRequest,
    ModuleRoleUpdateRequest,
    ModuleRoleVo,
    ModuleUpdateRequest,
    ModuleVo,
)
from .tenant_module import (
    AssignModuleRequest,
    TenantModuleListVo,
    TenantModuleVo,
)

__all__ = [
    # 模块
    "ModuleCreateRequest",
    "ModuleUpdateRequest",
    "ModuleVo",
    "ModuleListVo",
    # 模块菜单
    "ModuleMenuCreateRequest",
    "ModuleMenuUpdateRequest",
    "ModuleMenuVo",
    "ModuleMenuListVo",
    # 模块权限
    "ModulePermissionCreateRequest",
    "ModulePermissionUpdateRequest",
    "ModulePermissionVo",
    "ModulePermissionListVo",
    # 模块角色
    "ModuleRoleCreateRequest",
    "ModuleRoleUpdateRequest",
    "ModuleRolePermissionUpdateRequest",
    "ModuleRoleVo",
    "ModuleRoleListVo",
    # 租户模块分配
    "AssignModuleRequest",
    "TenantModuleVo",
    "TenantModuleListVo",
]
