"""插件默认模型配置"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import UniqueConstraint

from ai.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin


class PluginDefaultModel(
    BaseModel,
    AuditMixin,
    ActiveRecordMixin,
    TenantMixin,
):
    """插件默认模型配置"""

    __tablename__ = "plugin_default_models"
    __table_args__ = (
        UniqueConstraint("tenant_id", "model_type", name="uq_plugin_default_models_tenant_type"),
    )

    model_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="模型类型：llm, text-embedding, rerank 等",
    )

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID",
    )

    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="标准模型名称",
    )

    credential_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="关联的凭证ID",
    )

    custom_base_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="自定义 API 端点",
    )

    custom_model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="自定义模型名称",
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否有效",
    )
