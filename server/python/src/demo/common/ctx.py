"""
用户上下文

从 framework.common.ctx 模块导入。
"""

from pydantic import BaseModel, Field

# 从 framework 导入上下文管理
from framework.common.ctx import (
    Context,
    clear_context,
    get_context,
    get_tenant_id,
    get_user_id,
    set_context,
    set_user,
)


class User(BaseModel):
    """用户信息"""

    tenant_id: str = Field(..., description="租户ID")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")


__all__ = [
    "Context",
    "get_context",
    "set_context",
    "clear_context",
    "set_user",
    "get_user_id",
    "get_tenant_id",
    "User",
]
