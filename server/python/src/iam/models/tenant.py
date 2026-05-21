"""
租户模型

从 demo/models/tenant.py 迁移
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models import ActiveRecordMixin, BaseModel, TimestampMixin, UUIDPrimaryKeyMixin
from models.iam.enums import TenantStatus


class Tenant(
    BaseModel,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ActiveRecordMixin,
):
    """租户模型"""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="租户名称")
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="租户编码"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TenantStatus.ACTIVE, comment="状态"
    )

    # 联系人信息
    contact_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="联系人姓名"
    )
    contact_email: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="联系人邮箱"
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="联系人电话"
    )

    # 时间信息
    expired_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="过期时间"
    )

    # 扩展设置
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, comment="扩展设置"
    )

    __table_args__ = (
        Index("ix_tenants_code", "code"),
        Index("ix_tenants_status", "status"),
    )
