"""为 tenant_admins 表添加 role 字段

Revision ID: 004_add_admin_role
Revises: 003_module_menu_tree_fields
Create Date: 2026-06-22

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_admin_role"
down_revision: str | None = "003_module_menu_tree_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    """为 tenant_admins 表添加 role 字段"""
    op.add_column(
        "tenant_admins",
        sa.Column(
            "role",
            sa.String(50),
            nullable=False,
            server_default="ordinaryAdmin",
            comment="角色编码",
        ),
        schema=MODULE_SCHEMA,
    )


def downgrade() -> None:
    """回滚：删除 tenant_admins 表的 role 字段"""
    op.drop_column("tenant_admins", "role", schema=MODULE_SCHEMA)
