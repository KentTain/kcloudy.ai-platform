
"""
枚举类型

提供自定义枚举类型字段定义。
"""

from enum import Enum
from typing import Any, TypeVar

from sqlalchemy import String, TypeDecorator

T = TypeVar("T", bound=Enum)


class EnumType(TypeDecorator):
    """
    枚举类型

    数据库存储为字符串，Python 中为枚举对象。

    使用方式：
        status: Mapped[UserStatus] = mapped_column(
            EnumType(enum_class=UserStatus, length=20),
            comment="状态"
        )
    """

    impl = String
    cache_ok = True

    def __init__(self, enum_class: type[T], length: int = 64, **kwargs):
        """
        初始化枚举字段

        Args:
            enum_class: 枚举类
            length: 字符串长度限制，默认64
            **kwargs: 其他参数传递给String类型
        """
        self._enum_class = enum_class
        self._length = length
        super().__init__(length, **kwargs)

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        """
        处理绑定参数（Python -> 数据库）

        Args:
            value: Python枚举值
            dialect: 数据库方言

        Returns:
            str: 枚举的字符串值
        """
        if value is None:
            return None

        if isinstance(value, self._enum_class):
            return value.value

        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> T | None:
        """
        处理结果值（数据库 -> Python）

        Args:
            value: 数据库中的字符串值
            dialect: 数据库方言

        Returns:
            T: Python枚举实例
        """
        if value is None:
            return None

        try:
            return self._enum_class(value)
        except ValueError:
            return None

    def copy(self, **kw):
        """复制类型实例"""
        return EnumType(self._enum_class, length=self._length, **kw)
