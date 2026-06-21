"""
组织相关 Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from framework.schemas import BaseModel, TreeNodeTreeVo, TreeNodeVo
from pydantic import Field

if TYPE_CHECKING:
    from iam.models import Organization


class OrganizationCreate(BaseModel):
    """组织创建请求"""

    name: str = Field(..., min_length=1, max_length=100, description="组织名称")
    code: str | None = Field(None, max_length=50, description="组织编码")
    parent_id: str | None = Field(None, description="父组织 ID")
    sort_order: int | None = Field(None, ge=0, description="排序号")
    leader_id: str | None = Field(None, description="组织负责人 ID")


class OrganizationUpdate(BaseModel):
    """组织更新请求"""

    name: str | None = Field(None, max_length=100, description="组织名称")
    code: str | None = Field(None, max_length=50, description="组织编码")
    parent_id: str | None = Field(None, description="父组织 ID")
    sort_order: int | None = Field(None, ge=0, description="排序号")
    leader_id: str | None = Field(None, description="组织负责人 ID")
    status: str | None = Field(None, description="状态")


class OrganizationResponse(TreeNodeVo):
    """组织视图对象"""

    tenant_id: str
    name: str
    code: str | None
    sort_order: int
    leader_id: str | None
    status: str
    created_at: datetime


class OrganizationTreeResponse(TreeNodeTreeVo):
    """组织树形视图对象"""

    tenant_id: str
    name: str
    code: str | None
    sort_order: int
    leader_id: str | None
    status: str

    @classmethod
    def from_organization(cls, org: "Organization") -> "OrganizationTreeResponse":
        """从 Organization 实体构建 OrganizationTreeResponse

        Args:
            org: Organization 实体对象

        Returns:
            OrganizationTreeResponse 实例
        """
        return cls(
            id=org.id,
            parent_id=org.parent_id,
            parent_ids=org.parent_ids,
            tree_leaf=org.tree_leaf,
            tree_sorts=org.tree_sorts,
            tree_names=org.tree_names,
            tenant_id=org.tenant_id,
            name=org.name,
            code=org.code,
            sort_order=org.sort_order,
            leader_id=org.leader_id,
            status=org.status,
        )


class UserOrganizationRequest(BaseModel):
    """用户组织关联请求"""

    user_id: str = Field(..., description="用户 ID")
    is_leader: bool = Field(default=False, description="是否负责人")


class OrganizationUserResponse(BaseModel):
    """组织用户视图对象"""

    id: str
    user_id: str
    username: str
    nickname: str | None
    is_leader: bool


class OrganizationListItem(BaseModel):
    """组织列表项"""

    id: str = Field(..., description="组织 ID")
    name: str = Field(..., description="组织名称")
    code: str | None = Field(None, description="组织编码")
    parent_id: str | None = Field(None, description="父组织 ID")
    sort_order: int = Field(0, description="排序号")
    leader_id: str | None = Field(None, description="组织负责人 ID")
    status: str = Field("active", description="状态")

    @classmethod
    def from_organization(cls, org: Organization) -> OrganizationListItem:
        """从 Organization 实体构建 OrganizationListItem

        Args:
            org: Organization 实体对象

        Returns:
            OrganizationListItem 实例
        """
        return cls(
            id=org.id,
            name=org.name,
            code=org.code,
            parent_id=org.parent_id,
            sort_order=org.sort_order,
            leader_id=org.leader_id,
            status=org.status,
        )


class OrganizationListResponse(BaseModel):
    """组织列表响应"""

    items: list[OrganizationListItem] = Field(default_factory=list, description="组织列表")

    @classmethod
    def from_organizations(cls, organizations: list[Organization]) -> OrganizationListResponse:
        """从 Organization 列表构建 OrganizationListResponse

        Args:
            organizations: Organization 实体列表

        Returns:
            OrganizationListResponse 实例
        """
        return cls(items=[OrganizationListItem.from_organization(o) for o in organizations])


class OrganizationUserBatchRequest(BaseModel):
    """批量添加组织成员请求"""

    user_ids: list[str] = Field(..., min_length=1, description="用户 ID 列表")


class OrganizationDetailResponse(BaseModel):
    """组织详情响应（含统计信息）"""

    id: str
    name: str
    code: str | None
    parent_id: str | None
    sort_order: int
    leader_id: str | None
    status: str
    created_at: datetime
    path: str = Field("", description="组织路径")
    direct_member_count: int = Field(0, description="直属成员数")
    total_member_count: int = Field(0, description="累计成员数（含下级）")
    children_count: int = Field(0, description="直接子组织数")


class MemberInfo(BaseModel):
    """组织成员信息"""

    user_id: str
    username: str
    nickname: str | None
    email: str | None
    phone: str | None
    status: str
    is_leader: bool = False
