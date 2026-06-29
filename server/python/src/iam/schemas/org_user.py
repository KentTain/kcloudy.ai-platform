"""
组织人员相关 Pydantic Schemas

用于人员选择组件的组织人员树、用户搜索、组织搜索等 API。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from framework.schemas import BaseModel, BasePaginatedQuery, TreeNodeTreeVo, TreeNodeVo
from pydantic import Field

if TYPE_CHECKING:
    from iam.models import Organization, User


# ==============================================================================
# 用户简要信息
# ==============================================================================


class UserSimpleVo(BaseModel):
    """用户简要信息视图对象"""

    id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    nickname: str | None = Field(None, description="昵称")
    avatar: str | None = Field(None, description="头像 URL")
    email: str | None = Field(None, description="邮箱")
    status: str = Field(..., description="状态")
    org_id: str | None = Field(None, description="所属组织 ID")
    org_tree_names: str | None = Field(None, description="组织路径名称")

    @classmethod
    def from_user(
        cls,
        user: "User",
        org_id: str | None = None,
        org_tree_names: str | None = None,
    ) -> "UserSimpleVo":
        """从 User 实体构建 UserSimpleVo

        Args:
            user: User 实体对象
            org_id: 所属组织 ID（可选）
            org_tree_names: 组织路径名称（可选）

        Returns:
            UserSimpleVo 实例
        """
        return cls(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            avatar=user.avatar,
            email=user.email,
            status=user.status,
            org_id=org_id,
            org_tree_names=org_tree_names,
        )


# ==============================================================================
# 组织简要信息
# ==============================================================================


class OrganizationSimpleVo(TreeNodeVo):
    """组织简要信息视图对象"""

    tenant_id: str = Field(..., description="租户 ID")
    name: str = Field(..., description="组织名称")
    code: str | None = Field(None, description="组织编码")
    status: str = Field(..., description="状态")

    @classmethod
    def from_organization(cls, org: "Organization") -> "OrganizationSimpleVo":
        """从 Organization 实体构建 OrganizationSimpleVo

        Args:
            org: Organization 实体对象

        Returns:
            OrganizationSimpleVo 实例
        """
        return cls(
            id=org.id,
            parent_id=org.parent_id,
            parent_ids=org.parent_ids or "",
            tree_leaf=org.tree_leaf,
            tree_level=org.tree_level,
            tree_sort=org.tree_sort,
            tree_sorts=org.tree_sorts or "",
            tree_names=org.tree_names or "",
            tenant_id=org.tenant_id,
            name=org.name,
            code=org.code,
            status=org.status,
        )


# ==============================================================================
# 组织人员树
# ==============================================================================


class OrgUserTreeVo(TreeNodeTreeVo):
    """
    组织人员树节点视图对象

    继承 TreeNodeTreeVo，增加用户列表和统计字段。
    每个组织节点包含直属人员列表（users）和子组织列表（children）。
    """

    tenant_id: str = Field(..., description="租户 ID")
    name: str = Field(..., description="组织名称")
    code: str | None = Field(None, description="组织编码")
    status: str = Field(..., description="状态")
    has_org_num: int = Field(0, description="直属子组织数量")
    has_user_num: int = Field(0, description="直属人员数量")
    users: list[UserSimpleVo] = Field(default_factory=list, description="直属人员列表")

    @classmethod
    def from_organization(
        cls,
        org: "Organization",
        users: list[UserSimpleVo] | None = None,
        has_org_num: int = 0,
    ) -> "OrgUserTreeVo":
        """从 Organization 实体构建 OrgUserTreeVo

        Args:
            org: Organization 实体对象
            users: 直属人员列表（可选）
            has_org_num: 直属子组织数量（可选）

        Returns:
            OrgUserTreeVo 实例
        """
        user_list = users or []
        return cls(
            id=org.id,
            parent_id=org.parent_id,
            parent_ids=org.parent_ids or "",
            tree_leaf=org.tree_leaf,
            tree_level=org.tree_level,
            tree_sort=org.tree_sort,
            tree_sorts=org.tree_sorts or "",
            tree_names=org.tree_names or "",
            tenant_id=org.tenant_id,
            name=org.name,
            code=org.code,
            status=org.status,
            has_org_num=has_org_num,
            has_user_num=len(user_list),
            users=user_list,
        )


# ==============================================================================
# 请求模型
# ==============================================================================


class UserSearchQuery(BasePaginatedQuery):
    """用户搜索查询参数"""

    org_id: str | None = Field(None, description="组织 ID（可选，用于过滤组织下用户）")
    include_children: bool = Field(
        False, description="是否包含下级组织用户（仅当 org_id 有效时）"
    )


class OrgSearchQuery(BasePaginatedQuery):
    """组织搜索查询参数"""

    parent_id: str | None = Field(None, description="父组织 ID（可选）")


class OrgUsersQuery(BaseModel):
    """获取组织用户查询参数"""

    org_id: str = Field(..., description="组织 ID")
    include_children: bool = Field(False, description="是否包含下级组织用户")


class UserBatchBody(BaseModel):
    """批量获取用户请求体"""

    user_ids: list[str] = Field(..., min_length=1, description="用户 ID 列表")


class OrganizationBatchBody(BaseModel):
    """批量获取组织请求体"""

    org_ids: list[str] = Field(..., min_length=1, description="组织 ID 列表")


# ==============================================================================
# 响应模型
# ==============================================================================


class UserSimplePaginatedListResponse(BaseModel):
    """用户简要信息分页列表响应（人员选择组件专用）"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")
    items: list[UserSimpleVo] = Field(default_factory=list, description="用户列表")


class OrganizationPaginatedListResponse(BaseModel):
    """组织分页列表响应"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")
    items: list[OrganizationSimpleVo] = Field(
        default_factory=list, description="组织列表"
    )


class OrgUserTreeResponse(BaseModel):
    """组织人员树响应"""

    items: list[OrgUserTreeVo] = Field(default_factory=list, description="组织人员树")


class UserBatchResponse(BaseModel):
    """批量获取用户响应"""

    items: list[UserSimpleVo] = Field(default_factory=list, description="用户列表")


class OrganizationBatchResponse(BaseModel):
    """批量获取组织响应"""

    items: list[OrganizationSimpleVo] = Field(
        default_factory=list, description="组织列表"
    )
