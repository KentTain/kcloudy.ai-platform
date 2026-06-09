"""
租户业务配置模型
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class TenantBusinessConfig(BaseModel):
    """租户业务配置模型"""

    __tablename__ = "tenant_business_configs"

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="租户ID",
    )
    max_users: Mapped[int] = mapped_column(
        nullable=False, default=100, comment="最大用户数"
    )
    max_storage_mb: Mapped[int] = mapped_column(
        nullable=False, default=1024, comment="最大存储空间（MB）"
    )
    max_api_calls: Mapped[int] = mapped_column(
        nullable=False, default=10000, comment="最大API调用次数"
    )
