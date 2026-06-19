"""add tenant tables

Revision ID: 001_tenant
Revises:
Create Date: 2026-05-25

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_tenant"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    # 创建 tenant schema
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # 创建 tenants 表
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, comment="租户名称"),
        sa.Column("code", sa.String(50), unique=True, nullable=False, comment="租户编码"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="状态"),
        sa.Column("contact_name", sa.String(100), nullable=True, comment="联系人姓名"),
        sa.Column("contact_email", sa.String(128), nullable=True, comment="联系人邮箱"),
        sa.Column("contact_phone", sa.String(20), nullable=True, comment="联系人电话"),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True, comment="过期时间"),
        # 数据库配置
        sa.Column("db_type", sa.String(20), nullable=True, comment="数据库类型"),
        sa.Column("db_host", sa.String(255), nullable=True, comment="数据库主机"),
        sa.Column("db_port", sa.Integer, nullable=True, comment="数据库端口"),
        sa.Column("db_name", sa.String(100), nullable=True, comment="数据库名称"),
        sa.Column("db_username", sa.String(100), nullable=True, comment="数据库用户名"),
        sa.Column("db_password", sa.Text, nullable=True, comment="数据库密码(加密)"),
        # 存储配置
        sa.Column("storage_type", sa.String(20), nullable=True, comment="存储类型"),
        sa.Column("storage_bucket", sa.String(100), nullable=True, comment="存储桶名称"),
        # 缓存配置
        sa.Column("cache_db", sa.Integer, nullable=True, comment="Redis DB 编号"),
        # 加密密钥
        sa.Column("encryption_key", sa.Text, nullable=True, comment="租户加密密钥(主密钥加密)"),
        # 扩展设置
        sa.Column("settings", postgresql.JSONB, nullable=False, server_default="{}", comment="扩展设置"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenants_code", "tenants", ["code"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_status", "tenants", ["status"], schema=MODULE_SCHEMA)

    # 创建 tenant_configs 表
    op.create_table(
        "tenant_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("config_key", sa.String(100), nullable=False, comment="配置键"),
        sa.Column("config_value", postgresql.JSONB, nullable=True, comment="配置值"),
        sa.Column("description", sa.Text, nullable=True, comment="描述"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenant_configs_tenant_id", "tenant_configs", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("uq_tenant_configs_tenant_key", "tenant_configs", ["tenant_id", "config_key"], unique=True, schema=MODULE_SCHEMA)

    # 创建 tenant_admins 表
    op.create_table(
        "tenant_admins",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, comment="用户名"),
        sa.Column("password", sa.String(255), nullable=False, comment="密码哈希"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false", comment="是否默认管理员"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true", comment="是否激活"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenant_admins_username", "tenant_admins", ["username"], schema=MODULE_SCHEMA)


def downgrade() -> None:
    op.drop_table("tenant_admins", schema=MODULE_SCHEMA)
    op.drop_table("tenant_configs", schema=MODULE_SCHEMA)
    op.drop_table("tenants", schema=MODULE_SCHEMA)
    op.execute(f"DROP SCHEMA IF EXISTS {MODULE_SCHEMA} CASCADE")
