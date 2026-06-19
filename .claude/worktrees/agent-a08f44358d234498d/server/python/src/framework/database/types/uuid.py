"""
UUID 类型

提供 UUID 类型字段定义。
"""

import uuid
from typing import Any

from sqlalchemy import String, TypeDecorator


class StringUUID(TypeDecorator):
    """
    UUID 字符串类型

    数据库存储为字符串，Python 中为 UUID 对象。
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        """绑定参数时处理"""
        if value is None:
            return None

        if isinstance(value, uuid.UUID):
            return str(value)

        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> uuid.UUID | None:
        """获取结果时处理"""
        if value is None:
            return None

        if isinstance(value, uuid.UUID):
            return value

        return uuid.UUID(value)
