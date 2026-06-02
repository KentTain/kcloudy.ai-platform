"""
菜单模型

提供后端驱动的菜单系统，支持树形结构和权限关联。
"""

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from iam.models import BaseModel
from framework.database.mixins.tree import TreeNodeMixin


class Menu(BaseModel, TreeNodeMixin):
    """菜单模型"""

    __tablename__ = "menus"

    # 覆盖 TreeNodeMixin 的 parent_id
    # 注意：不添加外键约束，因为顶级节点的 parent_id 为虚拟根节点 "root"（不存在于数据库）
    # 树结构的父子关系通过 parent_ids 字段维护，应用层保证一致性
    parent_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, comment="父菜单ID"
    )

    module: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="所属模块标识（demo/iam/tenant）"
    )
    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="菜单编码（格式：module:name）"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="菜单名称（显示用）"
    )
    path: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="前端路由路径"
    )
    icon: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="图标标识"
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否显示"
    )
    deployment_base_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="模块部署地址（跨模块菜单）"
    )

    __table_args__ = (
        Index("ix_menus_parent_id", "parent_id"),
        Index("ix_menus_module", "module"),
        Index("ix_menus_code", "code"),
    )

    @classmethod
    def tree_name_field(cls) -> str:
        """返回名称字段"""
        return "name"


class MenuPermission(BaseModel):
    """菜单-权限关联模型"""

    __tablename__ = "menu_permissions"

    menu_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, comment="菜单ID"
    )
    permission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, comment="权限ID"
    )

    __table_args__ = (
        Index("ix_menu_permissions_menu_id", "menu_id"),
        Index("ix_menu_permissions_permission_id", "permission_id"),
        UniqueConstraint("menu_id", "permission_id", name="uq_menu_permissions_menu_permission"),
    )
