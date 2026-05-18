"""
用户上下文
"""

from contextvars import ContextVar

from pydantic import BaseModel, Field


class User(BaseModel):
    """用户信息"""

    tenant_id: str = Field(..., description="租户ID")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")


CTX_TOKEN: ContextVar[str | None] = ContextVar("token", default=None)
CTX_TENANT_ID: ContextVar[str | None] = ContextVar("tenant_id", default=None)
CTX_USER_ID: ContextVar[str | None] = ContextVar("user_id", default=None)
CTX_USER: ContextVar[User | None] = ContextVar("user", default=None)
