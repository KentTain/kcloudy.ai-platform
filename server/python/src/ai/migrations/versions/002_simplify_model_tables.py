"""简化模型表结构

Revision ID: 002
Revises: 001_ai_initial
Create Date: 2026-06-30

- 给 plugin_credentials 添加 is_default 字段
- 删除未使用的 model_providers 表
- 删除未使用的 model_configs 表
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "002_simplify_model_tables"
down_revision = "001_ai_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级：添加字段，删除表"""

    # 1. 给 plugin_credentials 添加 is_default 字段
    op.add_column(
        "plugin_credentials",
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否为默认凭证",
        ),
        schema="ai",
    )

    # 2. 创建索引
    op.create_index(
        "ix_plugin_credentials_is_default",
        "plugin_credentials",
        ["is_default"],
        schema="ai",
    )

    # 3. 删除未使用的表
    op.drop_table("model_configs", schema="ai")
    op.drop_table("model_providers", schema="ai")


def downgrade() -> None:
    """降级：恢复表，删除字段"""

    # 1. 重建 model_providers 表
    op.create_table(
        "model_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("provider_name", sa.String(255), nullable=False),
        sa.Column("provider_type", sa.String(64), nullable=False),
        sa.Column("plugin_id", sa.String(128), nullable=True),
        sa.Column("credentials", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        schema="ai",
    )

    # 2. 重建 model_configs 表
    op.create_table(
        "model_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("provider_id", sa.String(36), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("model_type", sa.String(32), nullable=False),
        sa.Column("parameters", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(["provider_id"], ["ai.model_providers.id"], ondelete="CASCADE"),
        schema="ai",
    )

    # 3. 创建索引
    op.create_index("ix_ai_model_providers_plugin_id", "model_providers", ["plugin_id"], schema="ai")
    op.create_index("ix_ai_model_providers_tenant_id", "model_providers", ["tenant_id"], schema="ai")
    op.create_index("ix_ai_model_configs_provider_id", "model_configs", ["provider_id"], schema="ai")
    op.create_index("ix_ai_model_configs_tenant_id", "model_configs", ["tenant_id"], schema="ai")

    # 4. 删除 is_default 字段
    op.drop_index("ix_plugin_credentials_is_default", schema="ai")
    op.drop_column("plugin_credentials", "is_default", schema="ai")
