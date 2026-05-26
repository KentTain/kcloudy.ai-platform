"""
租户配置模型

从 iam/models/tenant_config.py 迁移
"""

from typing import Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from tenant.models import BaseModel


class TenantConfig(BaseModel):
    """租户配置模型"""

    __tablename__ = "tenant_configs"

    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"
    )
    config_key: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="配置键"
    )
    config_value: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=True, comment="配置值"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="描述"
    )

    __table_args__ = (
        Index("ix_tenant_configs_tenant_id", "tenant_id"),
        Index("uq_tenant_configs_tenant_key", "tenant_id", "config_key", unique=True),
    )
