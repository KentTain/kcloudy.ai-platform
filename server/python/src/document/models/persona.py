"""人设模型"""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin


class Persona(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """人设表（AI 提示词）"""

    __tablename__ = "persona"
    __table_args__ = (Index("ix_persona_tenant_id", "tenant_id"), {"comment": "人设表"})

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="人设名称")
    role: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="角色定位")
    instruction: Mapped[str] = mapped_column(Text, nullable=False, comment="指令内容")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
