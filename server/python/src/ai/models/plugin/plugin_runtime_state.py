"""
插件运行时状态模型

存储进程信息、调用统计和冻结状态，与 Tenant 模块的管理面记录分离。
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin


class PluginRuntimeState(BaseModel, AuditMixin, ActiveRecordMixin, TenantMixin):
    """插件运行时状态模型"""

    __tablename__ = "plugin_runtime_states"
    __table_args__ = (
        UniqueConstraint("tenant_id", "plugin_id", name="uq_plugin_runtime_states_tenant_plugin"),
    )

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID",
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="inactive",
        comment="运行时状态",
    )
    process_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="进程ID",
    )
    port: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="运行端口",
    )
    call_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="调用次数统计",
    )
    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="错误次数统计",
    )
    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="最后错误信息",
    )
    last_started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后启动时间",
    )
    last_stopped_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后停止时间",
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后访问时间",
    )
    frozen_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="冻结时间",
    )
