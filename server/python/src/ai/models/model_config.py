"""
模型配置相关数据库模型

包含模型配置(ModelConfig)模型。
"""

from enum import Enum

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin

# ======================= 枚举定义 =======================


class ModelType(str, Enum):
    """模型类型枚举"""

    LLM = "llm"  # 大语言模型
    TEXT_EMBEDDING = "text-embedding"  # 文本嵌入模型
    RERANK = "rerank"  # 重排序模型
    SPEECH2TEXT = "speech2text"  # 语音转文本
    TTS = "tts"  # 文本转语音
    MODERATION = "moderation"  # 内容审核


# ======================= 模型定义 =======================


class ModelConfig(BaseModel, AuditMixin, ActiveRecordMixin, TenantMixin):
    """模型配置模型

    存储具体的模型配置信息，如 gpt-4、claude-3 等。
    每个配置关联一个模型提供商。
    """

    __tablename__ = "model_configs"

    provider_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ai.model_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联的模型提供商ID",
    )
    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="模型名称，如 gpt-4、claude-3-opus",
    )
    model_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="模型类型，如 llm、text-embedding、rerank",
    )
    parameters: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="默认参数配置，如 temperature、max_tokens",
    )
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否有效，用于软删除或禁用",
    )
