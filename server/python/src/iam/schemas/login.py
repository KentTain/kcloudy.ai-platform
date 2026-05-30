"""
登录相关 Pydantic Schemas
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""

    account: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="账号（用户名/邮箱/手机号）",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="密码",
    )


class LoginResponse(BaseModel):
    """登录响应"""

    access_token: str = Field(..., description="Access Token")
    refresh_token: str = Field(..., description="Refresh Token")
    expires_in: int = Field(..., description="Access Token 有效期（秒）")
    token_type: str = Field(default="Bearer", description="Token 类型")
    need_complete_profile: bool | None = Field(
        None, description="是否需要补全信息（OAuth 用户）"
    )
    tenant_id: str | None = Field(
        None, description="默认租户 ID"
    )


class LogoutRequest(BaseModel):
    """登出请求"""

    pass


class LogoutResponse(BaseModel):
    """登出响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(default="登出成功", description="消息")
