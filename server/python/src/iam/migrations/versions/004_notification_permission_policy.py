"""站内信/权限申请/企业策略表创建

Revision ID: 004_notification_permission_policy
Revises: 003_audit_log
Create Date: 2026-07-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_notification_permission_policy"
down_revision: str | None = "003_audit_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "iam"


def upgrade() -> None:
    """创建站内信、权限申请、企业策略相关表"""

    # ==================== 站内信表 ====================

    op.create_table(
        "notification",
        sa.Column("id", sa.String(36), primary_key=True),
        # TenantMixin
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True, comment="租户ID"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        # AuditMixin
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        # 业务字段
        sa.Column("title", sa.String(256), nullable=False, comment="通知标题"),
        sa.Column("content", sa.String(1024), nullable=True, comment="通知内容"),
        sa.Column("notification_type", sa.String(64), nullable=False, index=True, comment="通知类型"),
        sa.Column("recipient_id", sa.String(36), nullable=False, index=True, comment="接收人ID"),
        sa.Column("sender_id", sa.String(36), nullable=True, index=True, comment="发送人ID"),
        sa.Column("link", sa.String(512), nullable=True, comment="跳转链接"),
        sa.Column("extra_data", postgresql.JSONB, nullable=True, comment="扩展数据"),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false", index=True, comment="是否已读"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True, comment="已读时间"),
        # ActiveRecordMixin（软删除）
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
        schema=MODULE_SCHEMA,
        comment="站内信表",
    )
    op.create_index("ix_notification_tenant_id", "notification", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 站内信阅读状态表 ====================

    op.create_table(
        "notification_read",
        sa.Column("id", sa.String(36), primary_key=True),
        # TenantMixin
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True, comment="租户ID"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        # 业务字段
        sa.Column("user_id", sa.String(36), nullable=False, index=True, comment="用户ID"),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True, comment="最后已读时间"),
        sa.Column("unread_count", sa.Integer, nullable=False, server_default="0", comment="未读数量"),
        # ActiveRecordMixin（软删除）
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
        schema=MODULE_SCHEMA,
        comment="站内信阅读状态表",
    )
    op.create_index("ix_notification_read_tenant_id", "notification_read", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 权限申请表 ====================

    op.create_table(
        "permission_request",
        sa.Column("id", sa.String(36), primary_key=True),
        # TenantMixin
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True, comment="租户ID"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        # AuditMixin
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        # 业务字段
        sa.Column("applicant_id", sa.String(36), nullable=False, index=True, comment="申请人ID"),
        sa.Column("request_type", sa.String(64), nullable=False, index=True, comment="申请类型"),
        sa.Column("target_subject_type", sa.String(64), nullable=True, comment="目标主体类型"),
        sa.Column("target_subject_id", sa.String(64), nullable=True, comment="目标主体ID"),
        sa.Column("resource_type", sa.String(64), nullable=True, comment="资源类型"),
        sa.Column("resource_id", sa.String(64), nullable=True, comment="资源ID"),
        sa.Column("requested_actions", postgresql.ARRAY(sa.String(64)), nullable=True, comment="请求的操作列表"),
        sa.Column("request_payload", postgresql.JSONB, nullable=True, comment="申请附加数据"),
        sa.Column("reason", sa.String(512), nullable=True, comment="申请原因"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", index=True, comment="申请状态"),
        sa.Column("handler_id", sa.String(36), nullable=True, comment="审批人ID"),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True, comment="审批时间"),
        sa.Column("result_comment", sa.String(512), nullable=True, comment="审批意见"),
        # ActiveRecordMixin（软删除）
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
        schema=MODULE_SCHEMA,
        comment="权限申请表",
    )
    op.create_index("ix_permission_request_tenant_id", "permission_request", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 权限缓存失效事件表 ====================

    op.create_table(
        "permission_cache_event",
        sa.Column("id", sa.String(36), primary_key=True),
        # TenantMixin
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True, comment="租户ID"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        # 业务字段
        sa.Column("event_type", sa.String(64), nullable=False, index=True, comment="事件类型"),
        sa.Column("resource_type", sa.String(64), nullable=True, comment="资源类型"),
        sa.Column("resource_id", sa.String(64), nullable=True, comment="资源ID"),
        sa.Column("subject_type", sa.String(64), nullable=True, comment="主体类型"),
        sa.Column("subject_id", sa.String(64), nullable=True, comment="主体ID"),
        sa.Column("affected_scope", postgresql.JSONB, nullable=True, comment="影响范围"),
        sa.Column("payload", postgresql.JSONB, nullable=True, comment="事件数据"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", index=True, comment="处理状态"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True, comment="处理时间"),
        sa.Column("error_message", sa.String(512), nullable=True, comment="错误信息"),
        # ActiveRecordMixin（软删除）
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
        schema=MODULE_SCHEMA,
        comment="权限缓存失效事件表",
    )
    op.create_index("ix_permission_cache_event_tenant_id", "permission_cache_event", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 企业策略表 ====================

    op.create_table(
        "policy",
        sa.Column("id", sa.String(36), primary_key=True),
        # TenantMixin
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True, comment="租户ID"),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        # AuditMixin
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        # 业务字段
        sa.Column("code", sa.String(128), nullable=False, index=True, comment="策略编码"),
        sa.Column("name", sa.String(128), nullable=False, comment="策略名称"),
        sa.Column("policy_type", sa.String(64), nullable=False, index=True, comment="策略类型"),
        sa.Column("effect", sa.String(16), nullable=False, server_default="deny", comment="策略效果(allow/deny)"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="100", comment="优先级"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="false", comment="是否启用"),
        sa.Column("condition_json", postgresql.JSONB, nullable=True, comment="命中条件"),
        sa.Column("action_json", postgresql.JSONB, nullable=True, comment="动作配置"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True, comment="生效时间"),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True, comment="失效时间"),
        sa.Column("meta_data", postgresql.JSONB, nullable=True, comment="元数据"),
        # ActiveRecordMixin（软删除）
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
        schema=MODULE_SCHEMA,
        comment="企业策略表",
    )
    op.create_index("ix_policy_tenant_id", "policy", ["tenant_id"], schema=MODULE_SCHEMA)


def downgrade() -> None:
    """删除站内信、权限申请、企业策略相关表"""
    op.drop_table("policy", schema=MODULE_SCHEMA)
    op.drop_table("permission_cache_event", schema=MODULE_SCHEMA)
    op.drop_table("permission_request", schema=MODULE_SCHEMA)
    op.drop_table("notification_read", schema=MODULE_SCHEMA)
    op.drop_table("notification", schema=MODULE_SCHEMA)
