"""
时间类型

提供自定义时间类型字段定义。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, TypeDecorator


class UtcDateTime(TypeDecorator):
    """
    UTC 时间类型

    自动转换为 UTC 时间存储。
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> datetime | None:
        """绑定参数时处理"""
        if value is None:
            return None

        if isinstance(value, datetime):
            if value.tzinfo is not None:
                return value.astimezone(None).replace(tzinfo=None)
            return value

        return value

    def process_result_value(self, value: Any, dialect: Any) -> datetime | None:
        """获取结果时处理"""
        return value
