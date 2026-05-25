"""
权限模型
"""

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from iam.models import BaseModel


class Permission(BaseModel):
    """权限模型"""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="权限编码（如 user:read）"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="权限名称"
    )
    resource: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="资源名称（如 user, role）"
    )
    action: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="操作类型（read, write, delete）"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="权限描述"
    )

    __table_args__ = (
        Index("ix_permissions_code", "code"),
        Index("ix_permissions_resource", "resource"),
    )


class UserRole(BaseModel):
    """用户-角色关联模型"""

    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"
    )
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID"
    )

    __table_args__ = (
        Index("ix_user_roles_user_id", "user_id"),
        Index("ix_user_roles_role_id", "role_id"),
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )


class RolePermission(BaseModel):
    """角色-权限关联模型"""

    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID"
    )
    permission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, comment="权限ID"
    )

    __table_args__ = (
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
    )
