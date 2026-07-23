"""
站内信模型
"""

from datetime import datetime

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.datetime import UtcDateTime
from iam.models import BaseModel


class Notification(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """
    站内信表
    """

    __tablename__ = "notification"
    __table_args__ = ({"comment": "站内信表"},)

    title: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="通知标题",
    )
    content: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        comment="通知内容",
    )
    notification_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="通知类型",
    )
    recipient_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="接收人ID",
    )
    sender_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="发送人ID",
    )
    link: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="跳转链接",
    )
    extra_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="扩展数据",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="是否已读",
    )
    read_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime,
        nullable=True,
        comment="已读时间",
    )


class NotificationRead(BaseModel, TimestampMixin, TenantMixin, ActiveRecordMixin):
    """
    站内信阅读状态表
    """

    __tablename__ = "notification_read"
    __table_args__ = ({"comment": "站内信阅读状态表"},)

    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="用户ID",
    )
    last_read_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime,
        nullable=True,
        comment="最后已读时间",
    )
    unread_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="未读数量",
    )
