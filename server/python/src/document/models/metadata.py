"""元数据模型"""

from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import MetadataFieldType
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class LibraryMetadataField(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档库元数据字段定义表"""

    __tablename__ = "library_metadata_field"
    __table_args__ = (
        Index("ix_library_metadata_field_library_id", "library_id"),
        {"comment": "文档库元数据字段定义表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="文档库ID")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="字段名称")
    field_type: Mapped[str] = mapped_column(
        EnumType(enum_class=MetadataFieldType, length=20), nullable=False, comment="字段类型"
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否必填")
    enum_values: Mapped[list | None] = mapped_column(JSONB, nullable=True, comment="枚举值列表")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序")


class ResourceMetadata(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """资源元数据值表"""

    __tablename__ = "resource_metadata"
    __table_args__ = (
        Index("ix_resource_metadata_resource", "resource_type", "resource_id"),
        {"comment": "资源元数据值表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="文档库ID")
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="资源类型（folder/document）")
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="资源ID")
    field_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="元数据字段ID")
    field_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="字段名称（冗余）")
    value: Mapped[str | None] = mapped_column(String(1024), nullable=True, comment="元数据值")
