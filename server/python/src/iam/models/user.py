"""
用户模型
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.tenant import TenantMixin
from iam.models import BaseModel
from iam.models.enums import UserStatus
from framework.database.types.enum import EnumType


class User(BaseModel, ActiveRecordMixin, TenantMixin):
    """用户模型"""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_tenant_id", "tenant_id"),
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
        Index("ix_users_phone", "phone"),
        Index("ix_users_status", "status"),
        {"comment": "用户表"},
    )

    # 继承 TenantMixin 的 tenant_id，不添加外键约束
    # 跨模块外键在数据库层通过迁移脚本创建，ORM 层不定义以避免 MetaData 解析问题

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
        EnumType(enum_class=UserStatus, length=20), nullable=False, default=UserStatus.ACTIVE, comment="状态"
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

