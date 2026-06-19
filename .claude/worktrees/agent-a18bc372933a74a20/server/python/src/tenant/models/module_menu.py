"""
模块菜单定义模型
"""

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class ModuleMenu(BaseModel):
    """模块菜单定义模型"""

    __tablename__ = "module_menus"

    module_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        comment="模块ID",
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("module_menus.id", ondelete="SET NULL"),
        nullable=True,
        comment="父菜单ID",
    )
    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="菜单编码"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="菜单名称")
    path: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="前端路由路径"
    )
    icon: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="图标标识"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="排序号"
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否显示"
    )

    __table_args__ = (
        Index("ix_module_menus_code", "code"),
    )
