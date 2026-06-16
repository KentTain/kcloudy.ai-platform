"""
部门相关 Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from framework.schemas.tree import TreeNodeVo, TreeNodeTreeVo

if TYPE_CHECKING:
    from iam.models import Department


class DepartmentCreate(BaseModel):
    """部门创建请求"""

    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    code: str | None = Field(None, max_length=50, description="部门编码")
    parent_id: str | None = Field(None, description="父部门 ID")
    sort_order: int | None = Field(None, ge=0, description="排序号")
    leader_id: str | None = Field(None, description="部门负责人 ID")


class DepartmentUpdate(BaseModel):
    """部门更新请求"""

    name: str | None = Field(None, max_length=100, description="部门名称")
    code: str | None = Field(None, max_length=50, description="部门编码")
    parent_id: str | None = Field(None, description="父部门 ID")
    sort_order: int | None = Field(None, ge=0, description="排序号")
    leader_id: str | None = Field(None, description="部门负责人 ID")
    status: str | None = Field(None, description="状态")


class DepartmentResponse(TreeNodeVo):
    """部门视图对象"""

    tenant_id: str
    name: str
    code: str | None
    sort_order: int
    leader_id: str | None
    status: str
    created_at: datetime


class DepartmentTreeResponse(TreeNodeTreeVo):
    """部门树形视图对象"""

    tenant_id: str
    name: str
    code: str | None
    sort_order: int
    leader_id: str | None
    status: str


class UserDepartmentRequest(BaseModel):
    """用户部门关联请求"""

    user_id: str = Field(..., description="用户 ID")
    is_leader: bool = Field(default=False, description="是否部门负责人")


class DepartmentUserResponse(BaseModel):
    """部门用户视图对象"""

    id: str
    user_id: str
    username: str
    nickname: str | None
    is_leader: bool


class DepartmentListItem(BaseModel):
    """部门列表项"""

    id: str = Field(..., description="部门 ID")
    name: str = Field(..., description="部门名称")
    code: str | None = Field(None, description="部门编码")
    parent_id: str | None = Field(None, description="父部门 ID")
    sort_order: int = Field(0, description="排序号")
    leader_id: str | None = Field(None, description="部门负责人 ID")
    status: str = Field("active", description="状态")

    @classmethod
    def from_department(cls, dept: "Department") -> "DepartmentListItem":
        """从 Department 实体构建 DepartmentListItem

        Args:
            dept: Department 实体对象

        Returns:
            DepartmentListItem 实例
        """
        return cls(
            id=dept.id,
            name=dept.name,
            code=dept.code,
            parent_id=dept.parent_id,
            sort_order=dept.sort_order,
            leader_id=dept.leader_id,
            status=dept.status,
        )


class DepartmentListResponse(BaseModel):
    """部门列表响应"""

    items: list[DepartmentListItem] = Field(default_factory=list, description="部门列表")

    @classmethod
    def from_departments(cls, departments: list["Department"]) -> "DepartmentListResponse":
        """从 Department 列表构建 DepartmentListResponse

        Args:
            departments: Department 实体列表

        Returns:
            DepartmentListResponse 实例
        """
        return cls(items=[DepartmentListItem.from_department(d) for d in departments])