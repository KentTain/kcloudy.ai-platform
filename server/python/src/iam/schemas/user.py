"""
用户相关 Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from framework.schemas import BaseModel, BasePaginatedQuery, BaseQuery
from pydantic import EmailStr, Field, field_validator

if TYPE_CHECKING:
    from iam.models import Role


class UserRegisterRequest(BaseModel):
    """用户注册请求"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=32, description="密码")
    email: EmailStr | None = Field(None, description="邮箱")
    phone: str | None = Field(None, description="手机号")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v


class UserUpdate(BaseModel):
    """用户更新请求"""

    nickname: str | None = Field(None, max_length=100, description="昵称")
    avatar: str | None = Field(None, max_length=500, description="头像 URL")
    email: EmailStr | None = Field(None, description="邮箱")
    phone: str | None = Field(None, description="手机号")
    email_code: str | None = Field(None, description="邮箱验证码")
    phone_code: str | None = Field(None, description="手机验证码")


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""

    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=8, max_length=32, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v


class PasswordResetCodeRequest(BaseModel):
    """发送密码重置验证码请求"""

    email: EmailStr | None = Field(None, description="邮箱")
    phone: str | None = Field(None, description="手机号")


class PasswordResetRequest(BaseModel):
    """密码重置请求"""

    email: EmailStr | None = Field(None, description="邮箱")
    phone: str | None = Field(None, description="手机号")
    code: str = Field(..., description="验证码")
    new_password: str = Field(..., min_length=8, max_length=32, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v


class AdminUserCreate(BaseModel):
    """管理员创建用户请求"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=32)
    email: EmailStr | None = None
    phone: str | None = None
    nickname: str | None = Field(None, max_length=100)


class AdminUserUpdate(BaseModel):
    """管理员更新用户请求"""

    nickname: str | None = Field(None, max_length=100)
    avatar: str | None = Field(None, max_length=500)
    email: EmailStr | None = None
    phone: str | None = None


class UserStatusUpdateRequest(BaseModel):
    """用户状态更新请求"""

    status: str = Field(...)


class UserRoleAssignRequest(BaseModel):
    """用户角色分配请求"""

    role_ids: list[str] = Field(default_factory=list)


class UserOrganizationAssignRequest(BaseModel):
    """用户组织分配请求"""

    organization_ids: list[str] = Field(default_factory=list)


class AdminPasswordResetRequest(BaseModel):
    """管理员重置密码请求"""

    new_password: str | None = Field(None, min_length=8, max_length=32)


class AdminPasswordResetResponse(BaseModel):
    """管理员重置密码响应"""

    password: str


class UserQuery(BaseQuery):
    """用户列表查询参数"""

    status: str | None = Field(default=None, description="状态过滤")


class UserPaginatedQuery(UserQuery, BasePaginatedQuery):
    """用户分页查询参数"""

    org_id: str | None = Field(default=None, description="按组织 ID 筛选")
    include_children: bool = Field(default=False, description="是否包含下级组织用户")


class UserTenantResponse(BaseModel):
    """用户租户视图对象"""

    id: str = Field(..., description="租户 ID")
    name: str = Field(..., description="租户名称")
    code: str = Field(..., description="租户编码")
    is_default: bool = Field(False, description="是否默认租户")


class UserResponse(BaseModel):
    """用户视图对象"""

    id: str
    tenant_id: str
    username: str
    email: str | None
    phone: str | None
    nickname: str | None
    avatar: str | None
    status: str
    profile_completed: bool
    is_email_verified: bool
    is_phone_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    roles: list[str] = Field(default_factory=list, description="用户角色编码列表")
    permissions: list[str] = Field(default_factory=list, description="用户权限编码列表")
    tenants: list[UserTenantResponse] = Field(
        default_factory=list, description="用户所属租户列表"
    )


class UserDetailResponse(BaseModel):
    """用户详情聚合响应 Schema

    聚合用户基础信息、角色、权限、租户列表和菜单树的完整响应对象。
    由 Service 层聚合方法返回，Controller 直接使用。
    """

    id: str
    tenant_id: str
    username: str
    email: str | None
    phone: str | None
    nickname: str | None
    avatar: str | None
    status: str
    profile_completed: bool
    is_email_verified: bool
    is_phone_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    roles: list[str] = Field(default_factory=list, description="用户角色编码列表")
    permissions: list[str] = Field(default_factory=list, description="用户权限编码列表")
    tenants: list[UserTenantResponse] = Field(
        default_factory=list, description="用户所属租户列表"
    )
    menus: list[dict] = Field(default_factory=list, description="用户菜单树")

    @classmethod
    def from_user(
        cls,
        user: UserResponse,
        role_codes: list[str],
        permissions: list[str],
        tenants: list[UserTenantResponse],
        menus: list[dict] | None = None,
    ) -> UserDetailResponse:
        """从 User 实体和相关数据构建 UserDetailResponse

        Args:
            user: User 实体对象
            role_codes: 用户角色编码列表
            permissions: 用户权限编码列表
            tenants: 用户租户列表
            menus: 用户菜单树（可选）

        Returns:
            UserDetailResponse 实例
        """
        return cls(
            id=user.id,
            tenant_id=user.tenant_id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            nickname=user.nickname,
            avatar=user.avatar,
            status=user.status,
            profile_completed=user.profile_completed,
            is_email_verified=user.is_email_verified,
            is_phone_verified=user.is_phone_verified,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            roles=role_codes,
            permissions=permissions,
            tenants=tenants,
            menus=menus or [],
        )


class UserPaginatedListResponse(BaseModel):
    """用户分页列表响应"""

    total: int
    page: int
    page_size: int
    items: list[UserResponse]


class UserRoleItem(BaseModel):
    """用户角色项"""

    id: str = Field(..., description="角色 ID")
    code: str = Field(..., description="角色编码")
    name: str = Field(..., description="角色名称")
    description: str | None = Field(None, description="角色描述")

    @classmethod
    def from_role(cls, role: Role) -> UserRoleItem:
        """从 Role 实体构建 UserRoleItem

        Args:
            role: Role 实体对象

        Returns:
            UserRoleItem 实例
        """
        return cls(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
        )


class UserRolesResponse(BaseModel):
    """用户角色列表响应"""

    roles: list[UserRoleItem] = Field(default_factory=list, description="角色列表")

    @classmethod
    def from_roles(cls, roles: list[Role]) -> UserRolesResponse:
        """从 Role 列表构建 UserRolesResponse

        Args:
            roles: Role 实体列表

        Returns:
            UserRolesResponse 实例
        """
        return cls(roles=[UserRoleItem.from_role(r) for r in roles])


class UserStatsResponse(BaseModel):
    """用户统计响应"""

    total: int = Field(0, description="用户总数")
    enabled: int = Field(0, description="启用用户数")
    disabled: int = Field(0, description="停用用户数")
    multi_role: int = Field(0, description="多角色用户数")
