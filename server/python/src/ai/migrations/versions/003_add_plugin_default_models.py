"""添加 plugin_default_models 表

Revision ID: 003_add_plugin_default_models
Revises: 002_simplify_model_tables
Create Date: 2026-07-01
"""

from alembic import op
import sqlalchemy as sa

revision = "003_add_plugin_default_models"
down_revision = "002_simplify_model_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plugin_default_models",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("model_type", sa.String(32), nullable=False),
        sa.Column("plugin_id", sa.String(128), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=True),
        sa.Column("credential_id", sa.String(36), nullable=True),
        sa.Column("custom_base_url", sa.String(512), nullable=True),
        sa.Column("custom_model_name", sa.String(255), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.UniqueConstraint("tenant_id", "model_type", name="uq_plugin_default_models_tenant_type"),
        schema="ai",
    )

    op.create_index("ix_plugin_default_models_plugin_id", "plugin_default_models", ["plugin_id"], schema="ai")
    op.create_index("ix_plugin_default_models_credential_id", "plugin_default_models", ["credential_id"], schema="ai")


def downgrade() -> None:
    op.drop_index("ix_plugin_default_models_credential_id", schema="ai")
    op.drop_index("ix_plugin_default_models_plugin_id", schema="ai")
    op.drop_table("plugin_default_models", schema="ai")
