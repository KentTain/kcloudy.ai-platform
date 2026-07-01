"""
审计日志模型
"""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.datetime import UtcDateTime
from iam.models import BaseModel


class AuditLog(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """
    审计日志表
    """

    __tablename__ = "audit_log"
    __table_args__ = ({"comment": "审计日志表"},)

    business_domain: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="业务域（模块名称）",
    )
    business_domain_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="业务域ID",
    )
    permission_code: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        comment="权限编码",
    )
    operator_by: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="操作用户ID"
    )
    operator_name: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="操作用户名"
    )
    operated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, nullable=False, index=True, comment="操作时间"
    )
    operation_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="操作类型",
    )
    resource_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="资源类型",
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="主操作对象ID",
    )
    resource_name: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="主操作对象名称"
    )
    before_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="操作前数据"
    )
    after_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="操作后数据"
    )
    detail: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="操作详情"
    )
