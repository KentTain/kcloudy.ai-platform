"""审计日志表创建

Revision ID: 003_audit_log
Revises: 002_iam_enum_and_comment
Create Date: 2026-07-01

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003_audit_log"
down_revision = "002_iam_enum_and_comment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建审计日志表"""

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True, comment="主键ID"),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True, comment="租户ID"),
        sa.Column("business_domain", sa.String(64), nullable=False, index=True, comment="业务域"),
        sa.Column("business_domain_id", sa.String(64), nullable=True, index=True, comment="业务域ID"),
        sa.Column("permission_code", sa.String(128), nullable=True, comment="权限编码"),
        sa.Column("operator_by", sa.String(36), nullable=False, index=True, comment="操作用户ID"),
        sa.Column("operator_name", sa.String(256), nullable=False, comment="操作用户名"),
        sa.Column("operated_at", sa.DateTime(timezone=True), nullable=False, index=True, comment="操作时间"),
        sa.Column("operation_type", sa.String(64), nullable=False, comment="操作类型"),
        sa.Column("resource_type", sa.String(64), nullable=False, comment="资源类型"),
        sa.Column("resource_id", sa.String(64), nullable=True, index=True, comment="主操作对象ID"),
        sa.Column("resource_name", sa.String(256), nullable=False, comment="主操作对象名称"),
        sa.Column("before_data", sa.dialects.postgresql.JSONB, nullable=True, comment="操作前数据"),
        sa.Column("after_data", sa.dialects.postgresql.JSONB, nullable=True, comment="操作后数据"),
        sa.Column("detail", sa.dialects.postgresql.JSONB, nullable=True, comment="操作详情"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema="iam",
        comment="审计日志表",
    )

    op.create_index("ix_audit_log_permission_code", "audit_log", ["permission_code"], schema="iam")


def downgrade() -> None:
    """删除审计日志表"""

    op.drop_table("audit_log", schema="iam")
