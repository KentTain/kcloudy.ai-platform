"""
模块菜单权限关联模型
"""

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class ModuleMenuPermission(BaseModel):
    """模块菜单-权限关联模型"""

    __tablename__ = "module_menu_permissions"

    module_menu_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("module_menus.id", ondelete="CASCADE"),
        nullable=False,
        comment="模块菜单ID",
    )
    module_permission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("module_permissions.id", ondelete="CASCADE"),
        nullable=False,
        comment="模块权限ID",
    )

    __table_args__ = (
        UniqueConstraint(
            "module_menu_id",
            "module_permission_id",
            name="uq_module_menu_permissions_menu_perm"
    ),
        Index("ix_module_menu_permissions_menu_id", "module_menu_id"),
        Index("ix_module_menu_permissions_permission_id", "module_permission_id"),
        {"comment": "模块菜单-权限关联表"},
    )
