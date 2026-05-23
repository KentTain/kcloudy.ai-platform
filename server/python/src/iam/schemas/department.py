"""
部门相关 Pydantic Schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DepartmentCreateRequest(BaseModel):
    """部门创建请求"""

    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    code: str | None = Field(None, max_length=50, description="部门编码")
    parent_id: str | None = Field(None, description="父部门 ID")
    sort_order: int | None = Field(None, ge=0, description="排序号")
    leader_id: str | None = Field(None, description="部门负责人 ID")


class DepartmentUpdateRequest(BaseModel):
    """部门更新请求"""

    name: str | None = Field(None, max_length=100, description="部门名称")
    code: str | None = Field(None, max_length=50, description="部门编码")
    sort_order: int | None = Field(None, ge=0, description="排序号")
    leader_id: str | None = Field(None, description="部门负责人 ID")
    status: str | None = Field(None, description="状态")


class DepartmentVo(BaseModel):
    """部门视图对象"""

    id: str
    tenant_id: str
    parent_id: str | None
    name: str
    code: str | None
    sort_order: int
    leader_id: str | None
    status: str
    created_at: datetime


class DepartmentTreeVo(BaseModel):
    """部门树形视图对象"""

    id: str
    name: str
    code: str | None
    sort_order: int
    leader_id: str | None
    status: str
    children: list["DepartmentTreeVo"] = Field(default_factory=list)


class UserDepartmentRequest(BaseModel):
    """用户部门关联请求"""

    user_id: str = Field(..., description="用户 ID")
    is_leader: bool = Field(default=False, description="是否部门负责人")


class DepartmentUserVo(BaseModel):
    """部门用户视图对象"""

    id: str
    user_id: str
    username: str
    nickname: str | None
    is_leader: bool
