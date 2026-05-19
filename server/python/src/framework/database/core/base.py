"""
Base 模型类

提供统一的 SQLAlchemy Base 模型类。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    """
    基础模型类

    继承自 SQLAlchemy 的 DeclarativeBase 和 AsyncAttrs，提供：
    1. 异步属性访问支持
    2. 声明式模型定义
    """

    pass


class BaseModel(Base):
    """
    基础数据实体

    所有数据模型的基类，提供：
    1. UUID 主键支持
    2. 时间戳字段
    3. 基础操作方法
    """

    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="ID"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="创建时间"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
