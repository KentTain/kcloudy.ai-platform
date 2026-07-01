"""
模块级 Base 工厂函数

为每个模块创建带 schema 的 DeclarativeBase 和 BaseModel。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from framework.database.mixins.timestamp import TimestampMixin
from framework.database.mixins.uuid_primary_key import UUIDPrimaryKeyMixin


def create_module_base(schema: str) -> type[DeclarativeBase]:
    """
    为模块创建带 schema 的 DeclarativeBase

    Args:
        schema: PostgreSQL schema 名称

    Returns:
        配置了指定 schema 的 DeclarativeBase 子类

    Example:
        >>> Base = create_module_base("iam")
        >>> class User(Base):
        ...     __tablename__ = "users"
        ...     id: Mapped[str] = mapped_column(String(36), primary_key=True)
    """
    class ModuleBase(AsyncAttrs, DeclarativeBase):
        metadata = MetaData(schema=schema)

    return ModuleBase


def create_base_model(module_base: type) -> type:
    """
    为模块创建 BaseModel

    Args:
        module_base: 模块的 DeclarativeBase（由 create_module_base 创建）

    Returns:
        包含 id、created_at、updated_at 字段的抽象基类

    Example:
        >>> Base = create_module_base("iam")
        >>> BaseModel = create_base_model(Base)
        >>> class User(BaseModel):
        ...     __tablename__ = "users"
        ...     username: Mapped[str] = mapped_column(String(64))
    """
    class ModuleBaseModel(module_base, UUIDPrimaryKeyMixin, TimestampMixin):
        __abstract__ = True

        def to_dict(self) -> dict[str, Any]:
            """转换为字典，datetime 字段序列化为 ISO 格式字符串"""
            result = {}
            for column in self.__table__.columns:
                value = getattr(self, column.name)
                # 将 datetime 对象转换为 ISO 格式字符串
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value
            return result

    return ModuleBaseModel
