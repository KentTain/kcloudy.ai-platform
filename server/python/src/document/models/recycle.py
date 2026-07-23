"""回收站模型"""

from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import RecycleItemStatus, ResourceType
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class RecycleItem(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """回收站表"""

    __tablename__ = "recycle_item"
    __table_args__ = (
        Index("ix_recycle_item_library_id", "library_id"),
        Index("ix_recycle_item_status", "status"),
        {"comment": "回收站表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="源文档库ID")
    resource_type: Mapped[str] = mapped_column(
        EnumType(enum_class=ResourceType, length=20), nullable=False, comment="资源类型"
    )
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="资源ID")
    original_parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="原父资源ID")
    original_path: Mapped[str | None] = mapped_column(String(1024), nullable=True, comment="原路径")
    deleted_by: Mapped[str] = mapped_column(String(36), nullable=False, comment="删除人ID")
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=RecycleItemStatus, length=20), nullable=False,
        default=RecycleItemStatus.IN_RECYCLE, comment="状态",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="过期时间（自动清理）"
    )
    restored_by: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="恢复人ID")
    restored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="恢复时间")
