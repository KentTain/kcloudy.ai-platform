"""
自定义异常

从 framework.common 模块导入。
"""

# 从 framework 导入异常类
from framework.common.exceptions import (
    AppException,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)

__all__ = [
    "AppException",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "BadRequestError",
    "ServiceUnavailableError",
    "ValidationError",
    "ConflictError",
]
