"""
插件安装记录模型

对应 tenant schema 下的 plugin_installations 表，
作为租户级安装记录，仅包含管理面字段。
配置和运行时状态剥离到 AI Schema。
"""

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from tenant.models import BaseModel
from tenant.models.enums import PluginInstallationStatus, PluginInstallType
from framework.database.types.enum import EnumType


class TenantPluginInstallation(BaseModel, AuditMixin, ActiveRecordMixin, TenantMixin):
    """租户插件安装记录模型"""

    __tablename__ = "plugin_installations"

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID",
    )
    plugin_unique_identifier: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        index=True,
        comment="插件唯一标识符",
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="PENDING",
        comment="状态: PENDING, ACTIVE, INACTIVE, FAILED",
    )
    auto_start: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否自动启动",
    )
    freeze_threshold_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=24,
        comment="冻结阈值小时数",
    )
    plugin_type: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="插件类型",
    )
    runtime_type: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="运行时类型",
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "plugin_id", name="ix_plugin_installations_tenant_plugin"
        ),
        {"comment": "插件安装记录表"},
    )
