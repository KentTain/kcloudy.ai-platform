"""
角色模型
"""

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from iam.models import BaseModel


class Role(BaseModel):
    """角色模型"""

    __tablename__ = "roles"

    tenant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tenant.tenants.id", ondelete="CASCADE"), nullable=True, comment="租户ID（NULL 表示全局角色）"
    )
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="角色编码"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="角色名称"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="角色描述"
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否系统内置角色（不可删除）"
    )

    __table_args__ = (
        Index("ix_roles_tenant_id", "tenant_id"),
        Index("ix_roles_code", "code"),
    )
