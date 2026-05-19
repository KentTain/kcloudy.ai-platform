"""
审计混入

提供审计字段混入类。
"""

from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class AuditMixin:
    """
    审计混入类

    提供创建人和更新人字段。
    """

    __abstract__ = True

    created_by: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="创建人"
    )

    updated_by: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="更新人"
    )
