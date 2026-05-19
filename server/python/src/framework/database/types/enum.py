"""
枚举类型

提供自定义枚举类型字段定义。
"""

from enum import Enum
from typing import Any, Type, TypeVar

from sqlalchemy import String, TypeDecorator

T = TypeVar("T", bound=Enum)


class EnumType(TypeDecorator):
    """
    枚举类型

    数据库存储为字符串，Python 中为枚举对象。
    """

    impl = String(64)
    cache_ok = True

    def __init__(self, enum_class: Type[T], **kwargs):
        super().__init__(**kwargs)
        self._enum_class = enum_class

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        """绑定参数时处理"""
        if value is None:
            return None

        if isinstance(value, self._enum_class):
            return value.value

        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> T | None:
        """获取结果时处理"""
        if value is None:
            return None

        try:
            return self._enum_class(value)
        except ValueError:
            return None
