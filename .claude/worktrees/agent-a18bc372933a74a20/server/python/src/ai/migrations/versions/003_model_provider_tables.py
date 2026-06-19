"""add model provider tables

Revision ID: 003_model_provider
Revises: 002_plugin_fks
Create Date: 2026-06-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_model_provider"
down_revision: Union[str, None] = "002_plugin_fks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 模块 schema
MODULE_SCHEMA = "ai"


def upgrade() -> None:
    # 创建 model_providers 表（租户隔离）
    op.create_table(
        "model_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("provider_name", sa.String(255), nullable=False, comment="提供商名称"),
        sa.Column("provider_type", sa.String(64), nullable=False, comment="提供商类型"),
        sa.Column("plugin_id", sa.String(128), nullable=True, comment="关联的插件ID"),
        sa.Column("credentials", postgresql.JSONB, nullable=True, comment="凭证配置"),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default="true", comment="是否有效"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_model_providers_tenant_id", "model_providers", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_model_providers_plugin_id", "model_providers", ["plugin_id"], schema=MODULE_SCHEMA)

    # 创建 model_configs 表（租户隔离）
    op.create_table(
        "model_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("provider_id", sa.String(36), nullable=False, comment="关联的模型提供商ID"),
        sa.Column("model_name", sa.String(255), nullable=False, comment="模型名称"),
        sa.Column("model_type", sa.String(32), nullable=False, comment="模型类型"),
        sa.Column("parameters", postgresql.JSONB, nullable=True, comment="默认参数配置"),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default="true", comment="是否有效"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_model_configs_tenant_id", "model_configs", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_model_configs_provider_id", "model_configs", ["provider_id"], schema=MODULE_SCHEMA)

    # 创建同 schema 内的外键（model_configs.provider_id -> model_providers.id）
    op.create_foreign_key(
        constraint_name="fk_model_configs_provider_id",
        source_table="model_configs",
        referent_table="model_providers",
        local_cols=["provider_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema=MODULE_SCHEMA,
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # 删除外键
    op.drop_constraint("fk_model_configs_provider_id", "model_configs", schema=MODULE_SCHEMA, type_="foreignkey")

    # 删除表
    op.drop_table("model_configs", schema=MODULE_SCHEMA)
    op.drop_table("model_providers", schema=MODULE_SCHEMA)
