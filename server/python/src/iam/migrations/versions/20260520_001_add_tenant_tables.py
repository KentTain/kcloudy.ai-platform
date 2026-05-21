"""add tenant tables

Revision ID: 001_tenant
Revises:
Create Date: 2026-05-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_tenant"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
        sa.Column("settings", postgresql.JSONB, nullable=False, server_default="{}", comment="扩展设置"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_tenants_code", "tenants", ["code"])
    op.create_index("ix_tenants_status", "tenants", ["status"])

    # 创建 tenant_configs 表
    op.create_table(
        "tenant_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("config_key", sa.String(100), nullable=False, comment="配置键"),
        sa.Column("config_value", postgresql.JSONB, nullable=True, comment="配置值"),
        sa.Column("description", sa.Text, nullable=True, comment="描述"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_tenant_configs_tenant_id", "tenant_configs", ["tenant_id"])
    op.create_index("uq_tenant_configs_tenant_key", "tenant_configs", ["tenant_id", "config_key"], unique=True)

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
    )
    op.create_index("ix_tenant_admins_username", "tenant_admins", ["username"])

    # 创建 user_tenants 表
    op.create_table(
        "user_tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, comment="用户ID"),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false", comment="是否默认租户"),
        sa.Column("role", sa.String(20), nullable=False, server_default="member", comment="角色"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_user_tenants_user_id", "user_tenants", ["user_id"])
    op.create_index("ix_user_tenants_tenant_id", "user_tenants", ["tenant_id"])
    op.create_index("uq_user_tenants_user_tenant", "user_tenants", ["user_id", "tenant_id"], unique=True)


def downgrade() -> None:
    op.drop_table("user_tenants")
    op.drop_table("tenant_admins")
    op.drop_table("tenant_configs")
    op.drop_table("tenants")
