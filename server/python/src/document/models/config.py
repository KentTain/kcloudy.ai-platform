"""文档库配置模型"""

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin


class ConfigItem(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档库级配置表"""

    __tablename__ = "config_item"
    __table_args__ = (
        Index("ix_config_item_library_id", "library_id"),
        UniqueConstraint("library_id", "config_key", name="uq_config_item_library_key"),
        {"comment": "文档库级配置表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="文档库ID")
    config_key: Mapped[str] = mapped_column(String(128), nullable=False, comment="配置键")
    config_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="配置值")
