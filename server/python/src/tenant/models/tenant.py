"""
租户模型

从 iam/models/tenant.py 迁移
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from tenant.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from tenant.models.enums import TenantStatus


class Tenant(BaseModel, ActiveRecordMixin):
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

    # 数据库配置（物理隔离）
    db_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="数据库类型"
    )
    db_host: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="数据库主机"
    )
    db_port: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="数据库端口"
    )
    db_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="数据库名称"
    )
    db_username: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="数据库用户名"
    )
    db_password: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="数据库密码(加密)"
    )

    # 存储配置（物理隔离）
    storage_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="存储类型"
    )
    storage_bucket: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="存储桶名称"
    )

    # 缓存配置（物理隔离）
    cache_db: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Redis DB 编号"
    )

    # 资源配置关联（跨模块 FK，ORM 层不定义 ForeignKey 约束）
    db_config_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="数据库配置ID"
    )
    storage_config_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="存储配置ID"
    )
    cache_config_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="缓存配置ID"
    )
    queue_config_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="队列配置ID"
    )
    pubsub_config_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="发布订阅配置ID"
    )

    # 加密密钥
    encryption_key: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="租户加密密钥(主密钥加密)"
    )

    # 扩展设置
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, comment="扩展设置"
    )

    __table_args__ = (
        Index("ix_tenants_code", "code"),
        Index("ix_tenants_status", "status"),
    )
