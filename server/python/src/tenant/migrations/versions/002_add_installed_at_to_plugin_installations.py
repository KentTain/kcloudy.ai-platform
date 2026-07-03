"""添加 plugin_installations 表的 installed_at 字段

Revision ID: 002_add_installed_at
Revises: 001_tenant_initial
Create Date: 2026-07-03

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_add_installed_at"
down_revision: str | None = "001_tenant_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    """添加 installed_at 字段到 plugin_installations 表"""
    op.add_column(
        "plugin_installations",
        sa.Column(
            "installed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="安装完成时间",
        ),
        schema=MODULE_SCHEMA,
    )


def downgrade() -> None:
    """移除 installed_at 字段"""
    op.drop_column("plugin_installations", "installed_at", schema=MODULE_SCHEMA)
