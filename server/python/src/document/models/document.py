"""文档模型"""

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import DocumentProcessingStatus, DocumentStatus, DocumentType
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class Document(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档表"""

    __tablename__ = "document"
    __table_args__ = (
        Index("ix_document_library_id", "library_id"),
        Index("ix_document_folder_id", "folder_id"),
        Index("ix_document_lifecycle_status", "lifecycle_status"),
        {"comment": "文档表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="文档库ID")
    folder_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="文件夹ID（空为根目录）")
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="所有者用户ID")
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, comment="MinIO 存储键")
    name: Mapped[str] = mapped_column(String(256), nullable=False, comment="文档名称")
    document_type: Mapped[str] = mapped_column(
        EnumType(enum_class=DocumentType, length=20), nullable=False, comment="文档类型"
    )
    lifecycle_status: Mapped[str] = mapped_column(
        EnumType(enum_class=DocumentStatus, length=20), nullable=False,
        default=DocumentStatus.UPLOADING, comment="生命周期状态",
    )
    processing_status: Mapped[str] = mapped_column(
        EnumType(enum_class=DocumentProcessingStatus, length=20), nullable=False,
        default=DocumentProcessingStatus.PENDING_PARSE, comment="处理状态",
    )
    acl_inherit_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用权限继承"
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="文件大小（字节）")
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="MIME 类型")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="元数据")
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="切片索引任务ID")


class DocumentVersion(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档版本表"""

    __tablename__ = "document_version"
    __table_args__ = (Index("ix_document_version_document_id", "document_id"), {"comment": "文档版本表"})

    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="文档ID")
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="版本号")
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, comment="MinIO 存储键")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="文件大小")
    uploaded_by: Mapped[str] = mapped_column(String(36), nullable=False, comment="上传人ID")
