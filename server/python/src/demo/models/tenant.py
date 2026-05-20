"""
租户模型定义

包含 Tenant、TenantConfig、TenantAdmin、UserTenant 四个核心模型。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from demo.models import ActiveRecordMixin, BaseModel, TimestampMixin, UUIDPrimaryKeyMixin


class TenantStatus:
    """租户状态常量"""

    ACTIVE = "active"
    INACTIVE = "inactive"


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


class TenantConfig(
    BaseModel,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
):
    """租户配置模型"""

    __tablename__ = "tenant_configs"

    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"
    )
    config_key: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="配置键"
    )
    config_value: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=True, comment="配置值"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="描述"
    )

    __table_args__ = (
        Index("ix_tenant_configs_tenant_id", "tenant_id"),
        Index("uq_tenant_configs_tenant_key", "tenant_id", "config_key", unique=True),
    )


class TenantAdmin(
    BaseModel,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
):
    """租户管理员模型"""

    __tablename__ = "tenant_admins"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="用户名"
    )
    password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希"
    )
    is_default: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="是否默认管理员"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, nullable=False, comment="是否激活"
    )

    __table_args__ = (
        Index("ix_tenant_admins_username", "username"),
    )


class UserTenant(
    BaseModel,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
):
    """用户-租户关联模型"""

    __tablename__ = "user_tenants"

    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, comment="用户ID"
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"
    )
    is_default: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="是否默认租户"
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="member", comment="角色"
    )

    __table_args__ = (
        Index("ix_user_tenants_user_id", "user_id"),
        Index("ix_user_tenants_tenant_id", "tenant_id"),
        Index("uq_user_tenants_user_tenant", "user_id", "tenant_id", unique=True),
    )
