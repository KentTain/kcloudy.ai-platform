"""
租户模块分配模型
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class TenantModule(BaseModel):
    """租户模块分配模型"""

    __tablename__ = "tenant_modules"

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="租户ID",
    )
    module_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        comment="模块ID",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="生效时间"
    )
    expired_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="过期时间"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用"
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "module_id", name="uq_tenant_modules_tenant_module"
        ),
        {"comment": "租户模块分配表"},
    )
