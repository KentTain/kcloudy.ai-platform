"""
租户管理员模型

从 iam/models/tenant_admin.py 迁移
"""

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from tenant.models import BaseModel


class TenantAdmin(BaseModel):
    """租户管理员模型"""

    __tablename__ = "tenant_admins"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="用户名"
    )
    password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希"
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ordinaryAdmin", comment="角色编码"
    )
    is_default: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="是否默认管理员"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, nullable=False, comment="是否激活"
    )

    __table_args__ = (Index("ix_tenant_admins_username", "username"),)
