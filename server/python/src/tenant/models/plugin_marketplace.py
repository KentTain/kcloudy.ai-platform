"""插件市场配置模型"""

from datetime import datetime

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from tenant.models import BaseModel


class TenantPluginMarketplace(BaseModel, AuditMixin, ActiveRecordMixin):
    """插件市场配置模型

    存储远程插件市场的连接配置，支持 Dify、ModelScope 等多种市场类型。
    """

    __tablename__ = "plugin_marketplaces"

    name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="市场名称",
    )
    code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        unique=True,
        index=True,
        comment="市场编码",
    )
    type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="市场类型：dify, modelscope",
    )
    url: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="市场 API 地址",
    )
    auth_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="none",
        server_default="none",
        comment="认证类型：none, api_key, token",
    )
    auth_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="认证配置（加密存储）",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="是否启用",
    )
    sync_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="同步配置",
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        comment="最后同步时间",
    )
    last_sync_status: Mapped[str | None] = mapped_column(
        String(16),
        comment="最后同步状态",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        comment="市场描述",
    )

    __table_args__ = ({"comment": "插件市场配置表"},)
