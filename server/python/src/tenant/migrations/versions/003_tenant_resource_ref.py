"""remove tenant embedded config fields, add resource config references

Revision ID: 003_tenant_resource_ref
Revises: 002_tenant_module_system
Create Date: 2026-06-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_tenant_resource_ref"
down_revision: Union[str, None] = "002_tenant_module_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    # 添加资源配置关联字段
    op.add_column(
        "tenants",
        sa.Column("db_config_id", sa.String(36), nullable=True, comment="数据库配置ID"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("storage_config_id", sa.String(36), nullable=True, comment="存储配置ID"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("cache_config_id", sa.String(36), nullable=True, comment="缓存配置ID"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("queue_config_id", sa.String(36), nullable=True, comment="队列配置ID"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("pubsub_config_id", sa.String(36), nullable=True, comment="发布订阅配置ID"),
        schema=MODULE_SCHEMA,
    )

    # 删除内嵌配置字段
    op.drop_column("tenants", "cache_db", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "storage_bucket", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "storage_type", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "db_password", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "db_username", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "db_name", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "db_port", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "db_host", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "db_type", schema=MODULE_SCHEMA)


def downgrade() -> None:
    # 恢复内嵌配置字段
    op.add_column(
        "tenants",
        sa.Column("db_type", sa.String(20), nullable=True, comment="数据库类型"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("db_host", sa.String(255), nullable=True, comment="数据库主机"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("db_port", sa.Integer, nullable=True, comment="数据库端口"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("db_name", sa.String(100), nullable=True, comment="数据库名称"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("db_username", sa.String(100), nullable=True, comment="数据库用户名"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("db_password", sa.Text, nullable=True, comment="数据库密码(加密)"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("storage_type", sa.String(20), nullable=True, comment="存储类型"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("storage_bucket", sa.String(100), nullable=True, comment="存储桶名称"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "tenants",
        sa.Column("cache_db", sa.Integer, nullable=True, comment="Redis DB 编号"),
        schema=MODULE_SCHEMA,
    )

    # 删除资源配置关联字段
    op.drop_column("tenants", "pubsub_config_id", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "queue_config_id", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "cache_config_id", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "storage_config_id", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "db_config_id", schema=MODULE_SCHEMA)
