"""标签模型"""

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin


class TagGroup(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """标签分组表"""

    __tablename__ = "tag_group"
    __table_args__ = (Index("ix_tag_group_tenant_id", "tenant_id"), {"comment": "标签分组表"})

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="分组名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序")


class Tag(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """标签表"""

    __tablename__ = "tag"
    __table_args__ = (
        Index("ix_tag_tenant_id", "tenant_id"),
        Index("ix_tag_group_id", "group_id"),
        {"comment": "标签表"},
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="标签名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    color: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="颜色")
    group_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="分组ID")
    persona_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="引用人设ID")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", comment="状态")
    doc_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="引用文档数")
