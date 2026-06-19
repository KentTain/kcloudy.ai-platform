"""
OAuth 相关 Pydantic Schemas
"""

from pydantic import BaseModel, Field


class OAuthAuthorizeResponse(BaseModel):
    """OAuth 授权链接响应"""

    authorize_url: str = Field(..., description="授权链接")
    state: str = Field(..., description="状态参数（防 CSRF）")


class OAuthCallbackRequest(BaseModel):
    """OAuth 回调请求"""

    code: str = Field(..., description="授权码")
    state: str = Field(..., description="状态参数")


class OAuthCompleteProfileRequest(BaseModel):
    """OAuth 用户补全信息请求"""

    password: str = Field(..., min_length=8, max_length=32, description="密码")
    email: str | None = Field(None, description="邮箱")
    phone: str | None = Field(None, description="手机号")
    email_code: str | None = Field(None, description="邮箱验证码")
    phone_code: str | None = Field(None, description="手机验证码")


class OAuthBindRequest(BaseModel):
    """OAuth 账号绑定请求"""

    provider: str = Field(..., description="OAuth 提供商")
