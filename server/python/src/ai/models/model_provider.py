"""
模型提供商相关数据库模型

包含模型提供商(ModelProvider)模型。
"""

from enum import Enum

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin

# ======================= 枚举定义 =======================


class ProviderType(str, Enum):
    """提供商类型枚举"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    CUSTOM = "custom"


# ======================= 模型定义 =======================


class ModelProvider(BaseModel, AuditMixin, ActiveRecordMixin, TenantMixin):
    """模型提供商模型

    存储租户配置的 AI 模型提供商信息，如 OpenAI、Anthropic 等。
    每个租户可以配置多个提供商实例。
    """

    __tablename__ = "model_providers"

    provider_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="提供商名称，如 openai、anthropic",
    )
    provider_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="提供商类型，如 openai、anthropic、azure、custom",
    )
    plugin_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        comment="关联的插件ID，manifest中的author+name",
    )
    credentials: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="凭证配置（加密存储），包含API密钥等敏感信息",
    )
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否有效，用于软删除或禁用",
    )
