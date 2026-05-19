"""
租户混入

提供租户隔离字段混入类。
"""

from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column


class TenantMixin:
    """
    租户混入类

    提供租户 ID 字段，支持多租户隔离。
    """

    __abstract__ = True

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="租户ID"
    )

    __table_args__ = (
        Index("ix_tenant_id", "tenant_id"),
    )
