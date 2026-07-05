"""添加 message_metadata 表

Revision ID: 004_add_message_metadata_table
Revises: 003_add_plugin_default_models
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa

revision = "004_add_message_metadata_table"
down_revision = "003_add_plugin_default_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "message_metadata",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("message_id", sa.String(255), nullable=False),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("model_name", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(255), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("message_id", "tenant_id", name="uq_message_tenant"),
        schema="ai",
    )

    op.create_index("idx_message_metadata_message_id", "message_metadata", ["message_id"], schema="ai")
    op.create_index("idx_message_metadata_tenant_id", "message_metadata", ["tenant_id"], schema="ai")
    op.create_index("idx_message_metadata_user_id", "message_metadata", ["user_id"], schema="ai")
    op.create_index("idx_message_metadata_created_at", "message_metadata", ["created_at"], schema="ai")


def downgrade() -> None:
    op.drop_index("idx_message_metadata_created_at", schema="ai")
    op.drop_index("idx_message_metadata_user_id", schema="ai")
    op.drop_index("idx_message_metadata_tenant_id", schema="ai")
    op.drop_index("idx_message_metadata_message_id", schema="ai")
    op.drop_table("message_metadata", schema="ai")