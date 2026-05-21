"""
用户相关 Pydantic Schemas
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


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


class UserUpdateRequest(BaseModel):
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


class UserVo(BaseModel):
    """用户视图对象"""

    id: str
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


class UserListVo(BaseModel):
    """用户列表响应"""

    total: int
    items: list[UserVo]
