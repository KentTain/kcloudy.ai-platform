"""
权限模型
"""

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.tenant import TenantMixin
from iam.models import BaseModel


class Permission(BaseModel):
    """权限模型"""

    __tablename__ = "permissions"

    # 租户ID（NULL 表示全局权限）
    # 跨模块外键在数据库层通过迁移脚本创建，ORM 层不定义以避免 MetaData 解析问题
    tenant_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="租户ID（NULL 表示全局权限）"
    )
    code: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="权限编码（如 user:read）"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="权限名称")
    resource: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="资源名称（如 user, role）"
    )
    action: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="操作类型（read, write, delete）"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="权限描述"
    )
    # 模块定义层关联ID（跨模块 FK，ORM 层不定义 ForeignKey 约束）
    ref_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="模块定义层关联ID"
    )

    __table_args__ = (
        Index("ix_permissions_tenant_id", "tenant_id"),
        Index("ix_permissions_code", "code"),
        Index("ix_permissions_resource", "resource"),
        Index("ix_permissions_ref_id", "ref_id"),
        UniqueConstraint("tenant_id", "code", name="uq_permissions_tenant_code"),
        {"comment": "权限表"},
    )


class UserRole(BaseModel, TenantMixin):
    """用户-角色关联模型"""

    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        comment="角色ID",
    )

    __table_args__ = (
        Index("ix_user_roles_tenant_id", "tenant_id"),
        Index("ix_user_roles_user_id", "user_id"),
        Index("ix_user_roles_role_id", "role_id"),
        UniqueConstraint("tenant_id", "user_id", "role_id", name="uq_user_roles"),
        {"comment": "用户角色关联表"},
    )


class RolePermission(BaseModel, TenantMixin):
    """角色-权限关联模型"""

    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        comment="角色ID",
    )
    permission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        comment="权限ID",
    )

    __table_args__ = (
        Index("ix_role_permissions_tenant_id", "tenant_id"),
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
        UniqueConstraint(
            "tenant_id", "role_id", "permission_id", name="uq_role_permissions"
        ),
        {"comment": "角色权限关联表"},
    )
