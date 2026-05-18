"""
公共模块
"""

from demo.common.ctx import CTX_TENANT_ID, CTX_TOKEN, CTX_USER, CTX_USER_ID, User
from demo.common.exception_handler import register_exception_handlers
from demo.common.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)

__all__ = [
    "User",
    "CTX_TOKEN",
    "CTX_TENANT_ID",
    "CTX_USER_ID",
    "CTX_USER",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "BadRequestError",
    "register_exception_handlers",
]
