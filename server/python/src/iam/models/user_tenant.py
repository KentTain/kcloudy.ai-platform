"""
用户-租户关联模型

从 demo/models/tenant.py 迁移
"""

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from iam.models import BaseModel


class UserTenant(BaseModel):
    """用户-租户关联模型"""

    __tablename__ = "user_tenants"

    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, comment="用户ID"
    )
    # 租户 ID
    # 跨模块外键在数据库层通过迁移脚本创建，ORM 层不定义以避免 MetaData 解析问题
    tenant_id: Mapped[str] = mapped_column(
        String(36), nullable=False, comment="租户ID"
    )
    is_default: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="是否默认租户"
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="member", comment="角色"
    )

    __table_args__ = (
        Index("ix_user_tenants_user_id", "user_id"),
        Index("ix_user_tenants_tenant_id", "tenant_id"),
        Index("uq_user_tenants_user_tenant", "user_id", "tenant_id", unique=True),
    )
