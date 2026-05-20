"""
数据库模型基础类和 Mixins
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from demo.core.common.time import ChinaTimeZone


class BaseModel(DeclarativeBase):
    """SQLAlchemy 声明式基类"""

    pass


class TimestampMixin:
    """时间戳 Mixin"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class UUIDPrimaryKeyMixin:
    """UUID 主键 Mixin"""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键ID",
    )


class ActiveRecordMixin:
    """ActiveRecord 风格的便捷方法"""

    @classmethod
    async def create(
        cls, session: AsyncSession, source: dict[str, Any]
    ) -> "ActiveRecordMixin":
        """创建记录"""
        instance = cls(**source)
        session.add(instance)
        await session.flush()
        return instance

    async def update(
        self, session: AsyncSession, source: dict[str, Any]
    ) -> "ActiveRecordMixin":
        """更新记录"""
        for key, value in source.items():
            if hasattr(self, key):
                setattr(self, key, value)
        await session.flush()
        return self

    @classmethod
    async def one_by_id(
        cls, session: AsyncSession, id: str
    ) -> "ActiveRecordMixin | None":
        """根据 ID 查询单条记录"""
        from sqlalchemy import select

        stmt = select(cls).where(cls.id == id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def all(cls, session: AsyncSession) -> list["ActiveRecordMixin"]:
        """查询所有记录"""
        from sqlalchemy import select

        stmt = select(cls)
        result = await session.execute(stmt)
        return list(result.scalars().all())


from demo.models.tenant import (
    Tenant,
    TenantAdmin,
    TenantConfig,
    TenantStatus,
    UserTenant,
)

__all__ = [
    "ActiveRecordMixin",
    "BaseModel",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "Tenant",
    "TenantConfig",
    "TenantAdmin",
    "TenantStatus",
    "UserTenant",
]
