"""
模块角色定义模型
"""

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from . import BaseModel


class ModuleRole(BaseModel):
    """模块角色定义模型"""

    __tablename__ = "module_roles"

    module_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=True,
        comment="模块ID（NULL 表示全局角色）",
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="角色编码")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="角色名称")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="角色描述"
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否系统内置角色"
    )

    __table_args__ = (
        UniqueConstraint("module_id", "code", name="uq_module_roles_module_code"),
        # 全局角色唯一约束：当 module_id 为 NULL 时，code 必须唯一
        Index(
            "uq_module_roles_global_code",
            "code",
            unique=True,
            postgresql_where=expression.text("module_id IS NULL"),
        ),
    )
