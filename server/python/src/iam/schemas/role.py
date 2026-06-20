"""
角色相关 Pydantic Schemas
"""

from datetime import datetime

from framework.schemas import BaseModel, BasePaginatedQuery, BaseQuery
from pydantic import Field
from iam.schemas.permission import PermissionResponse


class RoleCreate(BaseModel):
    """角色创建请求"""

    code: str = Field(..., min_length=1, max_length=50, description="角色编码")
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    description: str | None = Field(None, description="角色描述")


class RoleUpdate(BaseModel):
    """角色更新请求"""

    name: str | None = Field(None, max_length=100, description="角色名称")
    description: str | None = Field(None, description="角色描述")


class RolePermissionRequest(BaseModel):
    """角色权限分配请求"""

    permission_ids: list[str] = Field(..., description="权限 ID 列表")


class RoleQuery(BaseQuery):
    """角色列表查询参数"""

    pass


class RolePaginatedQuery(RoleQuery, BasePaginatedQuery):
    """角色分页查询参数"""

    pass


class RoleResponse(BaseModel):
    """角色视图对象"""

    id: str
    tenant_id: str | None
    code: str
    name: str
    description: str | None
    is_system: bool
    created_at: datetime


class RolePaginatedListResponse(BaseModel):
    """角色分页列表响应"""

    total: int
    page: int
    page_size: int
    items: list[RoleResponse]


class RoleWithPermissionsResponse(BaseModel):
    """角色及其权限视图对象"""

    id: str
    tenant_id: str | None
    code: str
    name: str
    description: str | None
    is_system: bool
    permissions: list[PermissionResponse]
    created_at: datetime


class RoleOptionResponse(BaseModel):
    """角色选项视图对象（下拉列表用）"""

    id: str
    code: str
    name: str
    description: str | None


class RoleMemberAssignRequest(BaseModel):
    """角色成员分配请求"""

    user_ids: list[str] = Field(..., min_length=1, description="用户 ID 列表")


class RoleMenuAssignRequest(BaseModel):
    """角色菜单分配请求"""

    menu_ids: list[str] = Field(..., description="菜单 ID 列表")


class RoleMemberResponse(BaseModel):
    """角色成员视图对象"""

    user_id: str
    username: str
    nickname: str | None
    email: str | None
    phone: str | None
    status: str
