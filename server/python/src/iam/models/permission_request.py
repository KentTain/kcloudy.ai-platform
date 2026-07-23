"""
权限申请模型
"""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.datetime import UtcDateTime
from iam.models import BaseModel


class PermissionRequest(
    BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin
):
    """
    权限申请表
    """

    __tablename__ = "permission_request"
    __table_args__ = ({"comment": "权限申请表"},)

    applicant_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="申请人ID",
    )
    request_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="申请类型",
    )
    target_subject_type: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="目标主体类型",
    )
    target_subject_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="目标主体ID",
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="资源类型",
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="资源ID",
    )
    requested_actions: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(64)),
        nullable=True,
        comment="请求的操作列表",
    )
    request_payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="申请附加数据",
    )
    reason: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="申请原因",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        index=True,
        comment="申请状态",
    )
    handler_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="审批人ID",
    )
    handled_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime,
        nullable=True,
        comment="审批时间",
    )
    result_comment: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="审批意见",
    )


class PermissionCacheEvent(
    BaseModel, TimestampMixin, TenantMixin, ActiveRecordMixin
):
    """
    权限缓存失效事件表
    """

    __tablename__ = "permission_cache_event"
    __table_args__ = ({"comment": "权限缓存失效事件表"},)

    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="事件类型",
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="资源类型",
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="资源ID",
    )
    subject_type: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="主体类型",
    )
    subject_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="主体ID",
    )
    affected_scope: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="影响范围",
    )
    payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="事件数据",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        index=True,
        comment="处理状态",
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime,
        nullable=True,
        comment="处理时间",
    )
    error_message: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="错误信息",
    )
