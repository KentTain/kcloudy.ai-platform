"""
通用模块

包含异常、上下文、响应、单例等基础组件。
"""

from framework.common.exceptions import (
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    BadRequestError,
    ServiceUnavailableError,
)
from framework.common.responses import success_response, error_response
from framework.common.ctx import Context, get_context, set_context, clear_context
from framework.common.singleton import Singleton, AbstractSingleton
from framework.common.instance import get_instance_id, set_instance_id
from framework.common.time import ChinaTimeZone

__all__ = [
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "BadRequestError",
    "ServiceUnavailableError",
    "success_response",
    "error_response",
    "Context",
    "get_context",
    "set_context",
    "clear_context",
    "Singleton",
    "AbstractSingleton",
    "get_instance_id",
    "set_instance_id",
    "ChinaTimeZone",
]
