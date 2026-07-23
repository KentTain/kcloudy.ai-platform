"""
企业策略模型
"""

from datetime import datetime

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.datetime import UtcDateTime
from iam.models import BaseModel


class Policy(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """
    企业策略表
    """

    __tablename__ = "policy"
    __table_args__ = ({"comment": "企业策略表"},)

    code: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="策略编码",
    )
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="策略名称",
    )
    policy_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="策略类型",
    )
    effect: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="deny",
        comment="策略效果(allow/deny)",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="优先级",
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否启用",
    )
    condition_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="命中条件",
    )
    action_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="动作配置",
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime,
        nullable=True,
        comment="生效时间",
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime,
        nullable=True,
        comment="失效时间",
    )
    meta_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="元数据",
    )
