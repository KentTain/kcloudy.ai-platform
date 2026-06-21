"""
权限相关 Pydantic Schemas
"""

from datetime import datetime

from framework.schemas import BaseModel, BasePaginatedQuery, BaseQuery
from pydantic import Field


class PermissionQuery(BaseQuery):
    """权限列表查询参数"""

    pass


class PermissionPaginatedQuery(PermissionQuery, BasePaginatedQuery):
    """权限分页查询参数"""

    pass


class PermissionResponse(BaseModel):
    """权限视图对象"""

    id: str
    code: str
    name: str
    resource: str
    action: str
    description: str | None
    created_at: datetime


class PermissionListResponse(BaseModel):
    """权限列表响应"""

    permissions: list[PermissionResponse] = Field(default_factory=list, description="权限列表")


class PermissionPaginatedListResponse(BaseModel):
    """权限分页列表响应"""

    total: int
    page: int
    page_size: int
    items: list[PermissionResponse]


class PermissionGroupResponse(BaseModel):
    """按资源分组的权限视图对象"""

    resource: str = Field(..., description="资源名称")
    permissions: list[PermissionResponse] = Field(..., description="该资源的权限列表")
