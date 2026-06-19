"""会话模型"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel
from ai.models.enums import ConversationMode, ConversationStatus
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.types.enum import EnumType
from framework.database.types.uuid import StringUUID


class Conversation(BaseModel, ActiveRecordMixin, TenantMixin):
    """会话模型"""

    __tablename__ = "conversations"
    __table_args__ = ({ "schema": "ai", "comment": "会话" },)

    app_id: Mapped[str] = mapped_column(StringUUID, nullable=False, index=True, comment="应用id")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="会话名称")
    status: Mapped[ConversationStatus] = mapped_column(EnumType(enum_class=ConversationStatus), nullable=False, default=ConversationStatus.NORMAL, comment="状态")
    mode: Mapped[ConversationMode] = mapped_column(EnumType(enum_class=ConversationMode), nullable=False, default=ConversationMode.CHAT, comment="会话模式")
