"""消息模型"""

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel
from ai.models.enums import MessageRole, MessageStatus
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.types.enum import EnumType
from framework.database.types.uuid import StringUUID


class Message(BaseModel, ActiveRecordMixin, TenantMixin):
    """消息模型"""

    __tablename__ = "messages"
    __table_args__ = ({"schema": "ai", "comment": "消息"},)

    app_id: Mapped[str] = mapped_column(
        StringUUID, nullable=False, index=True, comment="应用id"
    )
    conversation_id: Mapped[str] = mapped_column(
        StringUUID,
        ForeignKey("ai.conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="会话id",
    )
    role: Mapped[MessageRole] = mapped_column(
        EnumType(enum_class=MessageRole), nullable=False, comment="角色"
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="消息内容")
    status: Mapped[MessageStatus] = mapped_column(
        EnumType(enum_class=MessageStatus),
        nullable=False,
        default=MessageStatus.PENDING,
        comment="状态",
    )
    query: Mapped[str | None] = mapped_column(Text, nullable=True, comment="用户问题")
    answer: Mapped[str | None] = mapped_column(Text, nullable=True, comment="助手回复")
    message_metadata: Mapped[dict | None] = mapped_column(
        postgresql.JSONB, nullable=True, comment="扩展元数据"
    )
    token_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=0, comment="token数量"
    )
