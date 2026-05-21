"""
权限相关 Pydantic Schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class PermissionVo(BaseModel):
    """权限视图对象"""

    id: str
    code: str
    name: str
    resource: str
    action: str
    description: str | None
    created_at: datetime


class PermissionListVo(BaseModel):
    """权限列表响应"""

    total: int
    items: list[PermissionVo]


class PermissionGroupVo(BaseModel):
    """按资源分组的权限视图对象"""

    resource: str = Field(..., description="资源名称")
    permissions: list[PermissionVo] = Field(..., description="该资源的权限列表")
