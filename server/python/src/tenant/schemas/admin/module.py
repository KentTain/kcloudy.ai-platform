"""
模块定义层 Schema

包含 Module、ModuleMenu、ModulePermission、ModuleRole 的请求和响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, Field

# =============================================================================
# 模块 Schema
# =============================================================================


class ModuleCreate(BaseModel):
    """创建模块请求"""

    code: str = Field(..., min_length=1, max_length=50, description="模块编码")
    name: str = Field(..., min_length=1, max_length=100, description="模块名称")
    description: str | None = Field(None, max_length=500, description="模块描述")
    icon: str | None = Field(None, max_length=100, description="图标标识")
    version: str = Field("1.0.0", max_length=20, description="模块版本")
    is_active: bool = Field(True, description="是否启用")
    is_need: bool = Field(False, description="是否必须模块")


class ModuleUpdate(BaseModel):
    """更新模块请求"""

    name: str | None = Field(None, min_length=1, max_length=100, description="模块名称")
    description: str | None = Field(None, max_length=500, description="模块描述")
    icon: str | None = Field(None, max_length=100, description="图标标识")
    version: str | None = Field(None, max_length=20, description="模块版本")
    is_active: bool | None = Field(None, description="是否启用")
    is_need: bool | None = Field(None, description="是否必须模块")


class ModuleResponse(BaseModel):
    """模块响应"""

    id: str = Field(..., description="模块ID")
    code: str = Field(..., description="模块编码")
    name: str = Field(..., description="模块名称")
    description: str | None = Field(None, description="模块描述")
    icon: str | None = Field(None, description="图标标识")
    version: str = Field(..., description="模块版本")
    is_active: bool = Field(..., description="是否启用")
    is_need: bool = Field(..., description="是否必须模块")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ModulePaginatedListResponse(BaseModel):
    """模块分页列表响应"""

    items: list[ModuleResponse] = Field(default_factory=list, description="模块列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


# =============================================================================
# 模块菜单 Schema
# =============================================================================


class ModuleMenuCreate(BaseModel):
    """创建模块菜单请求"""

    parent_id: str | None = Field(None, description="父菜单ID")
    code: str = Field(..., min_length=1, max_length=100, description="菜单编码")
    name: str = Field(..., min_length=1, max_length=100, description="菜单名称")
    path: str = Field(..., min_length=1, max_length=200, description="前端路由路径")
    icon: str | None = Field(None, max_length=100, description="图标标识")
    sort_order: int = Field(0, ge=0, description="排序号")
    is_visible: bool = Field(True, description="是否显示")


class ModuleMenuUpdate(BaseModel):
    """更新模块菜单请求"""

    parent_id: str | None = Field(None, description="父菜单ID")
    name: str | None = Field(None, min_length=1, max_length=100, description="菜单名称")
    path: str | None = Field(None, min_length=1, max_length=200, description="前端路由路径")
    icon: str | None = Field(None, max_length=100, description="图标标识")
    sort_order: int | None = Field(None, ge=0, description="排序号")
    is_visible: bool | None = Field(None, description="是否显示")


class ModuleMenuTreeResponse(BaseModel):
    """模块菜单响应"""

    id: str = Field(..., description="菜单ID")
    module_id: str = Field(..., description="模块ID")
    parent_id: str | None = Field(None, description="父菜单ID")
    code: str = Field(..., description="菜单编码")
    name: str = Field(..., description="菜单名称")
    path: str = Field(..., description="前端路由路径")
    icon: str | None = Field(None, description="图标标识")
    sort_order: int = Field(..., description="排序号")
    is_visible: bool = Field(..., description="是否显示")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    children: list["ModuleMenuTreeResponse"] = Field(default_factory=list, description="子菜单列表")


class ModuleMenuListResponse(BaseModel):
    """模块菜单列表响应（树形）"""

    items: list[ModuleMenuTreeResponse] = Field(default_factory=list, description="菜单树")


# =============================================================================
# 模块权限 Schema
# =============================================================================


class ModulePermissionCreate(BaseModel):
    """创建模块权限请求"""

    code: str = Field(..., min_length=1, max_length=100, description="权限编码")
    name: str = Field(..., min_length=1, max_length=100, description="权限名称")
    resource: str = Field(..., min_length=1, max_length=50, description="资源名称")
    action: str = Field(..., min_length=1, max_length=20, description="操作类型（read/write/delete）")
    description: str | None = Field(None, max_length=500, description="权限描述")


class ModulePermissionUpdate(BaseModel):
    """更新模块权限请求"""

    name: str | None = Field(None, min_length=1, max_length=100, description="权限名称")
    resource: str | None = Field(None, min_length=1, max_length=50, description="资源名称")
    action: str | None = Field(None, min_length=1, max_length=20, description="操作类型")
    description: str | None = Field(None, max_length=500, description="权限描述")


class ModulePermissionResponse(BaseModel):
    """模块权限响应"""

    id: str = Field(..., description="权限ID")
    module_id: str = Field(..., description="模块ID")
    code: str = Field(..., description="权限编码")
    name: str = Field(..., description="权限名称")
    resource: str = Field(..., description="资源名称")
    action: str = Field(..., description="操作类型")
    description: str | None = Field(None, description="权限描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ModulePermissionPaginatedListResponse(BaseModel):
    """模块权限分页列表响应"""

    items: list[ModulePermissionResponse] = Field(default_factory=list, description="权限列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


# =============================================================================
# 模块角色 Schema
# =============================================================================


class ModuleRoleCreate(BaseModel):
    """创建模块角色请求"""

    code: str = Field(..., min_length=1, max_length=50, description="角色编码")
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    description: str | None = Field(None, max_length=500, description="角色描述")
    is_system: bool = Field(False, description="是否系统内置角色")


class ModuleRoleUpdate(BaseModel):
    """更新模块角色请求"""

    name: str | None = Field(None, min_length=1, max_length=100, description="角色名称")
    description: str | None = Field(None, max_length=500, description="角色描述")


class ModuleRolePermissionUpdateRequest(BaseModel):
    """更新角色权限请求"""

    permission_ids: list[str] = Field(default_factory=list, description="权限ID列表")


class ModuleRoleResponse(BaseModel):
    """模块角色响应"""

    id: str = Field(..., description="角色ID")
    module_id: str = Field(..., description="模块ID")
    code: str = Field(..., description="角色编码")
    name: str = Field(..., description="角色名称")
    description: str | None = Field(None, description="角色描述")
    is_system: bool = Field(..., description="是否系统内置角色")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    permissions: list[ModulePermissionResponse] = Field(default_factory=list, description="权限列表")


class ModuleRolePaginatedListResponse(BaseModel):
    """模块角色分页列表响应"""

    items: list[ModuleRoleResponse] = Field(default_factory=list, description="角色列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


# =============================================================================
# 模块菜单权限 Schema
# =============================================================================


class ModuleMenuPermissionUpdateRequest(BaseModel):
    """更新菜单权限请求（整体替换）"""

    permission_ids: list[str] = Field(default_factory=list, description="权限ID列表")
