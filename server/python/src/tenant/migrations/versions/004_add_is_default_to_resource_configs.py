"""add is_default to resource configs

Revision ID: 004_resource_default
Revises: 003_tenant_resource_ref
Create Date: 2026-06-17

为五个资源配置表添加 is_default 字段和部分唯一索引。

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_resource_default"
down_revision: Union[str, None] = "003_tenant_resource_ref"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 模块 schema
MODULE_SCHEMA = "tenant"

# 资源配置表名列表
RESOURCE_CONFIG_TABLES = [
    "database_configs",
    "cache_configs",
    "storage_configs",
    "queue_configs",
    "pubsub_configs",
]


def upgrade() -> None:
    # 为五个表添加 is_default 字段
    for table in RESOURCE_CONFIG_TABLES:
        op.add_column(
            table,
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false", comment="是否为默认配置"),
            schema=MODULE_SCHEMA,
        )

    # 创建部分唯一索引（PostgreSQL partial unique index，确保每张表最多只有一条 is_default=TRUE 的记录）
    op.create_index(
        "uix_database_configs_default",
        "database_configs",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "uix_cache_configs_default",
        "cache_configs",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "uix_storage_configs_default",
        "storage_configs",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "uix_queue_configs_default",
        "queue_configs",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "uix_pubsub_configs_default",
        "pubsub_configs",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
        schema=MODULE_SCHEMA,
    )


def downgrade() -> None:
    # 删除部分唯一索引（逆序）
    op.drop_index("uix_pubsub_configs_default", table_name="pubsub_configs", schema=MODULE_SCHEMA)
    op.drop_index("uix_queue_configs_default", table_name="queue_configs", schema=MODULE_SCHEMA)
    op.drop_index("uix_storage_configs_default", table_name="storage_configs", schema=MODULE_SCHEMA)
    op.drop_index("uix_cache_configs_default", table_name="cache_configs", schema=MODULE_SCHEMA)
    op.drop_index("uix_database_configs_default", table_name="database_configs", schema=MODULE_SCHEMA)

    # 删除 is_default 字段（逆序）
    for table in reversed(RESOURCE_CONFIG_TABLES):
        op.drop_column(table, "is_default", schema=MODULE_SCHEMA)
