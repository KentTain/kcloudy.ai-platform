"""
模块菜单定义模型
"""

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins import TreeNodeMixin

from . import BaseModel


class ModuleMenu(BaseModel, TreeNodeMixin):
    """模块菜单定义模型"""

    __tablename__ = "module_menus"

    module_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        comment="模块ID",
    )
    # 覆盖 TreeNodeMixin 的 parent_id，保持外键约束
    # 注意：不添加外键约束，因为顶级节点的 parent_id 为虚拟根节点 "root"（不存在于数据库）
    # 树结构的父子关系通过 parent_ids 字段维护，应用层保证一致性
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("module_menus.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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
    is_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否显示"
    )

    __table_args__ = (
        Index("ix_module_menus_code", "code"),
    )

    @classmethod
    def tree_name_field(cls) -> str:
        """返回名称字段"""
        return "name"
