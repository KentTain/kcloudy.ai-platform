"""
模块角色权限关联模型
"""

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class ModuleRolePermission(BaseModel):
    """模块角色权限关联模型"""

    __tablename__ = "module_role_permissions"

    module_role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("module_roles.id", ondelete="CASCADE"),
        nullable=False,
        comment="模块角色ID",
    )
    module_permission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("module_permissions.id", ondelete="CASCADE"),
        nullable=False,
        comment="模块权限ID",
    )

    __table_args__ = (
        UniqueConstraint(
            "module_role_id",
            "module_permission_id",
            name="uq_module_role_permissions_role_perm",
        ),
        Index("ix_module_role_permissions_role_id", "module_role_id"),
        Index("ix_module_role_permissions_permission_id", "module_permission_id"),
    )
