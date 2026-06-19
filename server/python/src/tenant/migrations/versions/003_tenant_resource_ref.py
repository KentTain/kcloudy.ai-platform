"""remove tenant embedded config fields, add resource config references

Revision ID: 003_tenant_resource_ref
Revises: 002_tenant_module_system
Create Date: 2026-06-11

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_tenant_resource_ref"
down_revision: str | None = "002_tenant_module_system"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    # 注意：db_config_id 等 5 个资源配置关联字段已在 002_tenant_module_system.py 中添加
    # 这里只需删除内嵌配置字段

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

    # 注意：不删除 db_config_id 等 5 个资源配置关联字段
    # 这些字段在 002_tenant_module_system.py 中添加，应在那里删除
