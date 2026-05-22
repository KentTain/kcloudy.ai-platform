"""add tenant resource config

Revision ID: 003_tenant_resource
Revises: 002_iam
Create Date: 2026-05-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_tenant_resource"
down_revision: Union[str, None] = "002_iam"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加租户资源配置字段"""
    # 数据库配置字段
    op.add_column(
        "tenants",
        sa.Column("db_type", sa.String(20), nullable=True, comment="数据库类型"),
    )
    op.add_column(
        "tenants",
        sa.Column("db_host", sa.String(255), nullable=True, comment="数据库主机"),
    )
    op.add_column(
        "tenants",
        sa.Column("db_port", sa.Integer, nullable=True, comment="数据库端口"),
    )
    op.add_column(
        "tenants",
        sa.Column("db_name", sa.String(100), nullable=True, comment="数据库名称"),
    )
    op.add_column(
        "tenants",
        sa.Column("db_username", sa.String(100), nullable=True, comment="数据库用户名"),
    )
    op.add_column(
        "tenants",
        sa.Column("db_password", sa.Text, nullable=True, comment="数据库密码(加密)"),
    )

    # 存储配置字段
    op.add_column(
        "tenants",
        sa.Column("storage_type", sa.String(20), nullable=True, comment="存储类型"),
    )
    op.add_column(
        "tenants",
        sa.Column("storage_bucket", sa.String(100), nullable=True, comment="存储桶名称"),
    )

    # 缓存配置字段
    op.add_column(
        "tenants",
        sa.Column("cache_db", sa.Integer, nullable=True, comment="Redis DB 编号"),
    )

    # 加密密钥字段
    op.add_column(
        "tenants",
        sa.Column("encryption_key", sa.Text, nullable=True, comment="租户加密密钥(主密钥加密)"),
    )


def downgrade() -> None:
    """移除租户资源配置字段"""
    op.drop_column("tenants", "encryption_key")
    op.drop_column("tenants", "cache_db")
    op.drop_column("tenants", "storage_bucket")
    op.drop_column("tenants", "storage_type")
    op.drop_column("tenants", "db_password")
    op.drop_column("tenants", "db_username")
    op.drop_column("tenants", "db_name")
    op.drop_column("tenants", "db_port")
    op.drop_column("tenants", "db_host")
    op.drop_column("tenants", "db_type")
