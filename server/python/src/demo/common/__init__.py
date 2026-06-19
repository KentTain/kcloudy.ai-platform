"""
公共模块

从 framework.common 模块导入。
"""

from demo.common.ctx import User
from demo.common.exception_handler import register_exception_handlers
from demo.common.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)

# 从 framework 提供的上下文管理函数
from framework.common.ctx import (
    clear_context,
    get_context,
    get_tenant_id,
    get_user_id,
    set_context,
)

__all__ = [
    "User",
    "get_context",
    "set_context",
    "clear_context",
    "get_user_id",
    "get_tenant_id",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "BadRequestError",
    "register_exception_handlers",
]
