"""
OAuth 关联模型
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from iam.models import BaseModel
from iam.models.enums import OAuthProvider
from framework.database.types.enum import EnumType


class OAuthConnection(BaseModel):
    """OAuth 关联模型"""

    __tablename__ = "oauth_connections"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"
    )
    provider: Mapped[str] = mapped_column(
        EnumType(enum_class=OAuthProvider, length=20), nullable=False, comment="OAuth 提供商（wechat, wework）"
    )
    provider_user_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="第三方用户ID（openid / unionid）"
    )
    access_token: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="访问令牌"
    )
    refresh_token: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="刷新令牌"
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="令牌过期时间"
    )

    __table_args__ = (
        Index("ix_oauth_connections_user_id", "user_id"),
        Index("ix_oauth_connections_provider", "provider"),
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
        {"comment": "OAuth关联表"},
    )
