"""
Base 模型类

提供统一的 SQLAlchemy Base 模型类。
"""

from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
