"""文档库权限模型"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import LibraryRoleKind, ResourceAclEffect, ResourceAclStatus, ResourceType
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class LibraryRole(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档库权限组表"""

    __tablename__ = "library_role"
    __table_args__ = (
        Index("ix_library_role_library_id", "library_id"),
        Index("ix_library_role_kind", "role_kind"),
        {"comment": "文档库权限组表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="文档库ID")
    role_kind: Mapped[str] = mapped_column(
        EnumType(enum_class=LibraryRoleKind, length=20), nullable=False, comment="权限组类型"
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, comment="权限组编码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="权限组名称")
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="描述")
    system_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否系统内置")
    permissions: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="权限定义（动作->等级）")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", comment="状态")


class LibraryRoleMember(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """权限组成员表"""

    __tablename__ = "library_role_member"
    __table_args__ = (
        Index("ix_library_role_member_role_id", "role_id"),
        Index("ix_library_role_member_user_id", "user_id"),
        {"comment": "权限组成员表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="文档库ID")
    role_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="权限组ID")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="用户ID")


class ResourceAcl(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """资源访问控制表（资源权限继承链）"""

    __tablename__ = "resource_acl"
    __table_args__ = (
        Index("ix_resource_acl_library_id", "library_id"),
        Index("ix_resource_acl_resource", "resource_type", "resource_id"),
        Index("ix_resource_acl_subject", "subject_id"),
        {"comment": "资源访问控制表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="文档库ID")
    resource_type: Mapped[str] = mapped_column(
        EnumType(enum_class=ResourceType, length=20), nullable=False, comment="资源类型"
    )
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="资源ID")
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="主体ID（用户ID/角色ID）")
    subject_type: Mapped[str] = mapped_column(String(20), nullable=False, default="user", comment="主体类型")
    action: Mapped[str] = mapped_column(String(64), nullable=False, comment="动作（read/preview/download/edit）")
    effect: Mapped[str] = mapped_column(
        EnumType(enum_class=ResourceAclEffect, length=20), nullable=False, comment="效果"
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="优先级")
    inherited_from_resource_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="继承来源资源ID"
    )
    condition_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="条件")
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=ResourceAclStatus, length=20), nullable=False,
        default=ResourceAclStatus.ACTIVE, comment="状态",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="过期时间"
    )
