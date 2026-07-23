"""文件夹模型"""

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import FolderLifecycleStatus
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.mixins.tree import TreeNodeMixin
from framework.database.types.enum import EnumType


class Folder(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin, TreeNodeMixin):
    """文件夹表（树形，TreeNodeMixin）"""

    __tablename__ = "folder"
    __table_args__ = (
        Index("ix_folder_library_id", "library_id"),
        Index("ix_folder_lifecycle_status", "lifecycle_status"),
        {"comment": "文件夹表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="文档库ID")
    name: Mapped[str] = mapped_column(String(256), nullable=False, comment="文件夹名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    lifecycle_status: Mapped[str] = mapped_column(
        EnumType(enum_class=FolderLifecycleStatus, length=20), nullable=False,
        default=FolderLifecycleStatus.ACTIVE, comment="生命周期状态",
    )
    acl_inherit_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用权限继承"
    )
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否敏感"
    )
    doc_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="文档数")
