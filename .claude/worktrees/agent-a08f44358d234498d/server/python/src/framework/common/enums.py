"""
通用枚举定义
"""

from enum import Enum
from typing import TypedDict


class EnumMemberData(TypedDict):
    """枚举成员数据结构"""

    name: str
    value: str
    label: str


class EnumBase(Enum):
    """枚举基类，提供通用的枚举功能"""

    @classmethod
    def get_enum_list(cls) -> list[EnumMemberData]:
        """获取枚举成员列表"""
        return [
            EnumMemberData(name=member.name, value=member.value, label=member.label)
            for member in cls
        ]

    @property
    def label(self) -> str:
        """获取枚举成员的显示标签"""
        return self.name


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
