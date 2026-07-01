"""创建审计日志表

Revision ID: 003_iam_audit_log
Revises: 002_iam_enum_and_comment
Create Date: 2026-07-01

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_iam_audit_log"
down_revision: str | None = "002_iam_enum_and_comment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "iam"


def upgrade() -> None:
    # 创建 audit_log 表
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("business_domain", sa.String(64), nullable=False, comment="业务域"),
        sa.Column("business_domain_id", sa.String(64), nullable=True, comment="业务域ID"),
        sa.Column("operator_by", sa.String(36), nullable=False, comment="操作用户ID"),
        sa.Column("operator_name", sa.String(256), nullable=False, comment="操作用户名"),
        sa.Column("operated_at", sa.DateTime(timezone=True), nullable=False, comment="操作时间"),
        sa.Column("operation_type", sa.String(64), nullable=False, comment="操作类型"),
        sa.Column("resource_type", sa.String(64), nullable=False, comment="资源类型"),
        sa.Column("resource_id", sa.String(64), nullable=True, comment="主操作对象ID"),
        sa.Column("resource_name", sa.String(256), nullable=False, comment="主操作对象名称"),
        sa.Column("before_data", postgresql.JSONB, nullable=True, comment="操作前数据"),
        sa.Column("after_data", postgresql.JSONB, nullable=True, comment="操作后数据"),
        sa.Column("details", postgresql.JSONB, nullable=True, comment="操作详情"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )

    # 创建索引
    op.create_index("ix_audit_log_tenant_id", "audit_log", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_audit_log_business_domain", "audit_log", ["business_domain"], schema=MODULE_SCHEMA)
    op.create_index("ix_audit_log_operator_by", "audit_log", ["operator_by"], schema=MODULE_SCHEMA)
    op.create_index("ix_audit_log_operated_at", "audit_log", ["operated_at"], schema=MODULE_SCHEMA)
    op.create_index("ix_audit_log_operation_type", "audit_log", ["operation_type"], schema=MODULE_SCHEMA)
    op.create_index("ix_audit_log_resource_type", "audit_log", ["resource_type"], schema=MODULE_SCHEMA)
    op.create_index("ix_audit_log_resource_id", "audit_log", ["resource_id"], schema=MODULE_SCHEMA)

    # 添加表级 comment
    op.execute("COMMENT ON TABLE iam.audit_log IS '审计日志表'")


def downgrade() -> None:
    # 删除 audit_log 表
    op.drop_table("audit_log", schema=MODULE_SCHEMA)
