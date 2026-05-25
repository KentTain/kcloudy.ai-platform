"""
用户模型
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from iam.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from iam.models.enums import UserStatus


class User(BaseModel, ActiveRecordMixin):
    """用户模型"""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="用户名"
    )
    email: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, comment="邮箱"
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True, comment="手机号"
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="密码哈希（OAuth 用户可为空）"
    )
    nickname: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="昵称"
    )
    avatar: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="头像 URL"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=UserStatus.ACTIVE, comment="状态"
    )
    profile_completed: Mapped[bool] = mapped_column(
        default=True, nullable=False, comment="信息是否完整（OAuth 用户首次登录为 FALSE）"
    )
    is_email_verified: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="邮箱是否已验证"
    )
    is_phone_verified: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="手机是否已验证"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后登录时间"
    )
    last_login_ip: Mapped[str | None] = mapped_column(
        String(45), nullable=True, comment="最后登录 IP"
    )

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
        Index("ix_users_phone", "phone"),
        Index("ix_users_status", "status"),
    )
