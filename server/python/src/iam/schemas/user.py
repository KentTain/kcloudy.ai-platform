"""
用户相关 Pydantic Schemas
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from framework.schemas.base import BaseQuery, BasePaginatedQuery


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


class UserDepartmentAssignRequest(BaseModel):
    """用户部门分配请求"""

    department_ids: list[str] = Field(default_factory=list)


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

    pass


class UserTenantResponse(BaseModel):
    """用户租户视图对象"""

    id: str = Field(..., description="租户 ID")
    name: str = Field(..., description="租户名称")
    code: str = Field(..., description="租户编码")
    is_default: bool = Field(False, description="是否默认租户")


class UserResponse(BaseModel):
    """用户视图对象"""

    model_config = ConfigDict(from_attributes=True)

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
    tenants: list[UserTenantResponse] = Field(default_factory=list, description="用户所属租户列表")


class UserPaginatedListResponse(BaseModel):
    """用户分页列表响应"""

    total: int
    page: int
    page_size: int
    items: list[UserResponse]
