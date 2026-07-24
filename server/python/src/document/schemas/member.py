"""成员 Schema"""

from datetime import datetime

from pydantic import Field

from framework.schemas import BaseModel


class MemberCreate(BaseModel):
    """添加成员请求"""

    user_id: str = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户名")
    role: str = Field(default="member", description="角色")
    remarks: str | None = Field(default=None, description="备注")


class MemberRoleUpdate(BaseModel):
    """更新成员角色请求"""

    role: str = Field(..., description="新角色")


class MemberResponse(BaseModel):
    """成员响应"""

    id: str
    library_id: str
    user_id: str
    user_name: str
    role: str
    status: str = "active"
    remarks: str | None = None
    created_at: datetime | None = None
