"""
模块权限定义模型
"""

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class ModulePermission(BaseModel):
    """模块权限定义模型"""

    __tablename__ = "module_permissions"

    module_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        comment="模块ID",
    )
    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="权限编码"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="权限名称")
    resource: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="资源名称"
    )
    action: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="操作类型（read/write/delete）"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="权限描述"
    )

    __table_args__ = (
        Index("ix_module_permissions_code", "code"),
    )
