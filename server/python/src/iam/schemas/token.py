"""
Token 相关 Pydantic Schemas
"""

from framework.schemas import BaseModel
from pydantic import Field


class TokenRefreshRequest(BaseModel):
    """Token 刷新请求"""

    refresh_token: str = Field(..., description="Refresh Token")


class TokenRefreshResponse(BaseModel):
    """Token 刷新响应"""

    access_token: str = Field(..., description="新的 Access Token")
    refresh_token: str = Field(..., description="新的 Refresh Token")
    expires_in: int = Field(..., description="Access Token 有效期（秒）")
    token_type: str = Field(default="Bearer", description="Token 类型")


class TokenPayload(BaseModel):
    """Token 载荷"""

    user_id: str = Field(..., description="用户 ID")
    session_id: str = Field(..., description="会话 ID")
    version: int = Field(..., description="版本号")
    roles: list[str] = Field(default_factory=list, description="角色列表")
    permissions: list[str] = Field(default_factory=list, description="权限列表")
