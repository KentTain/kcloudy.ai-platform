"""
通用枚举定义
"""

from enum import Enum


class ErrorCode(str, Enum):
    """错误代码枚举"""

    SUCCESS = "0"
    UNKNOWN_ERROR = "1"
    INVALID_PARAMETER = "1001"
    RESOURCE_NOT_FOUND = "1002"
    PERMISSION_DENIED = "1003"
    AUTHENTICATION_FAILED = "1004"
    RESOURCE_ALREADY_EXISTS = "1005"
    OPERATION_FAILED = "1006"


class Status(str, Enum):
    """通用状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    DELETED = "deleted"
    ARCHIVED = "archived"


class BooleanType(str, Enum):
    """布尔类型枚举"""

    TRUE = "true"
    FALSE = "false"


class SortOrder(str, Enum):
    """排序方向枚举"""

    ASC = "asc"
    DESC = "desc"
