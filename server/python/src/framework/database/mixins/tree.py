"""
树结构混入

提供树形结构字段混入类。
"""

from sqlalchemy import String, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column


class TreeMixin:
    """
    树结构混入类

    提供树形结构的 parent_id、level、path 字段。
    """

    __abstract__ = True

    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="父节点ID"
    )

    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="层级"
    )

    path: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="路径（逗号分隔的ID列表）"
    )

    __table_args__ = (
        Index("ix_parent_id", "parent_id"),
    )

    def is_root(self) -> bool:
        """是否为根节点"""
        return self.parent_id is None

    def get_ancestors(self) -> list[str]:
        """获取祖先节点 ID 列表"""
        if not self.path:
            return []
        return [p for p in self.path.split(",") if p]
