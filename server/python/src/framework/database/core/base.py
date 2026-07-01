"""
Base 模型类

提供统一的 SQLAlchemy Base 模型类。
"""

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from framework.database.mixins.timestamp import TimestampMixin
from framework.database.mixins.uuid_primary_key import UUIDPrimaryKeyMixin


class Base(AsyncAttrs, DeclarativeBase):
    """
    基础模型类

    继承自 SQLAlchemy 的 DeclarativeBase 和 AsyncAttrs，提供：
    1. 异步属性访问支持
    2. 声明式模型定义
    """

    pass


class BaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    基础数据实体（默认 public schema）

    所有数据模型的基类，提供：
    1. UUID 主键支持
    2. 时间戳字段
    3. 基础操作方法
    """

    __abstract__ = True

    def to_dict(self, exclude: list[str] | None = None) -> dict[str, Any]:
        """
        将模型转换为字典

        Args:
            exclude: 需要排除的字段列表

        Returns:
            模型数据字典
        """
        exclude = exclude or []
        result = {}

        for column in self.__table__.columns:
            # 跳过排除字段
            if column.name in exclude:
                continue

            value = getattr(self, column.name)

            # 处理特殊类型
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, enum.Enum):
                value = value.value
            elif isinstance(value, UUID):
                value = str(value)

            result[column.name] = value

        return result
