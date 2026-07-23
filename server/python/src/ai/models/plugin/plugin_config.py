"""
插件配置模型

存储插件能力定义和持久化配置，与 Tenant 模块的管理面记录分离。
"""

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin


class PluginConfig(BaseModel, AuditMixin, ActiveRecordMixin, TenantMixin):
    """插件配置模型"""

    __tablename__ = "plugin_configs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "plugin_id", name="uq_plugin_configs_tenant_plugin"),
    )

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID",
    )
    plugin_unique_identifier: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="插件唯一标识符",
    )
    plugin_config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="插件能力定义和持久化配置",
    )
    runtime_config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="运行时配置",
    )
