"""
枚举工具函数
"""

from enum import Enum
from typing import Any


def get_enum_values(enum_class: type[Enum]) -> list[Any]:
    """
    获取枚举类的所有值

    Args:
        enum_class: 枚举类

    Returns:
        list: 枚举值列表

    Example:
        >>> from enum import Enum
        >>> class Status(str, Enum):
        ...     ACTIVE = "active"
        ...     INACTIVE = "inactive"
        >>> get_enum_values(Status)
        ['active', 'inactive']
    """
    return [member.value for member in enum_class]


def get_enum_names(enum_class: type[Enum]) -> list[str]:
    """
    获取枚举类的所有名称

    Args:
        enum_class: 枚举类

    Returns:
        list: 枚举名称列表
    """
    return [member.name for member in enum_class]


def is_valid_enum_value(value: Any, enum_class: type[Enum]) -> bool:
    """
    检查值是否是有效的枚举值

    Args:
        value: 要检查的值
        enum_class: 枚举类

    Returns:
        bool: 是否有效
    """
    try:
        enum_class(value)
        return True
    except ValueError:
        return False


def get_enum_member(enum_class: type[Enum], value: Any) -> Enum | None:
    """
    根据值获取枚举成员

    Args:
        enum_class: 枚举类
        value: 枚举值

    Returns:
        Enum | None: 枚举成员，无效则返回 None
    """
    try:
        return enum_class(value)
    except ValueError:
        return None


def get_enum_by_name(enum_class: type[Enum], name: str) -> Enum | None:
    """
    根据名称获取枚举成员

    Args:
        enum_class: 枚举类
        name: 枚举名称

    Returns:
        Enum | None: 枚举成员，无效则返回 None
    """
    try:
        return enum_class[name]
    except KeyError:
        return None


def enum_to_dict(enum_class: type[Enum]) -> dict[str, Any]:
    """
    将枚举类转换为字典

    Args:
        enum_class: 枚举类

    Returns:
        dict: {name: value} 字典
    """
    return {member.name: member.value for member in enum_class}


def enum_to_choices(enum_class: type[Enum]) -> list[dict[str, Any]]:
    """
    将枚举类转换为选项列表（用于前端下拉框等）

    Args:
        enum_class: 枚举类

    Returns:
        list: [{label, value}, ...] 列表
    """
    return [
        {"label": member.name, "value": member.value}
        for member in enum_class
    ]
