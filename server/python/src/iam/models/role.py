"""
角色模型
"""

from sqlalchemy import Boolean, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from iam.models import BaseModel


class Role(BaseModel):
    """角色模型"""

    __tablename__ = "roles"

    # 租户 ID（NULL 表示全局角色）
    # 跨模块外键在数据库层通过迁移脚本创建，ORM 层不定义以避免 MetaData 解析问题
    tenant_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="租户ID（NULL 表示全局角色）"
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="角色编码")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="角色名称")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="角色描述"
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否系统内置角色（不可删除）"
    )
    # 模块定义层关联ID（跨模块 FK，ORM 层不定义 ForeignKey 约束）
    ref_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="模块定义层关联ID"
    )

    __table_args__ = (
        Index("ix_roles_tenant_id", "tenant_id"),
        Index("ix_roles_code", "code"),
        Index("ix_roles_ref_id", "ref_id"),
        UniqueConstraint("tenant_id", "code", name="uq_roles_tenant_code"),
        {"comment": "角色表"},
    )
