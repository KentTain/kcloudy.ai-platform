"""文档库模型"""

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import LibraryMemberRole, LibraryMemberStatus, LibraryType
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class Library(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档库表（personal/team）"""

    __tablename__ = "library"
    __table_args__ = (
        Index("ix_library_tenant_id", "tenant_id"),
        Index("ix_library_type", "type"),
        Index("ix_library_owner_id", "owner_id"),
        {"comment": "文档库表"},
    )

    type: Mapped[str] = mapped_column(
        EnumType(enum_class=LibraryType, length=20), nullable=False, comment="文档库类型"
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="文档库编码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="文档库名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="图标")
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="所有者用户ID")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")
    allow_submit_to_kb: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否允许提交入库"
    )


class LibraryMember(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档库成员表"""

    __tablename__ = "library_member"
    __table_args__ = (
        Index("ix_library_member_library_id", "library_id"),
        Index("ix_library_member_user_id", "user_id"),
        Index("ix_library_member_role", "role"),
        {"comment": "文档库成员表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="文档库ID")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="用户ID")
    user_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="用户名")
    role: Mapped[str] = mapped_column(
        EnumType(enum_class=LibraryMemberRole, length=20), nullable=False, comment="成员角色"
    )
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=LibraryMemberStatus, length=20), nullable=False,
        default=LibraryMemberStatus.ACTIVE, comment="成员状态",
    )
    remarks: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="备注")
