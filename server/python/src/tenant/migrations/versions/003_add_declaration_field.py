"""补充 declaration 字段并移除 remote_declaration

Revision ID: 003_add_declaration_field
Revises: 002_tenant_plugins
Create Date: 2026-06-25

新增 declaration 字段（合并 remote_declaration）
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_add_declaration_field"
down_revision: str | None = "002_tenant_plugins"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    """升级：添加 declaration 字段，删除 remote_declaration 字段"""

    # 1. 添加 declaration 字段
    op.add_column(
        "plugin_definitions",
        sa.Column(
            "declaration",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="完整声明内容（manifest + 工具/模型声明）",
        ),
        schema=MODULE_SCHEMA,
    )

    # 2. 删除 remote_declaration 字段
    op.drop_column("plugin_definitions", "remote_declaration", schema=MODULE_SCHEMA)


def downgrade() -> None:
    """回滚：恢复 remote_declaration 字段，删除 declaration 字段"""

    # 1. 恢复 remote_declaration 字段
    op.add_column(
        "plugin_definitions",
        sa.Column(
            "remote_declaration",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="远程声明",
        ),
        schema=MODULE_SCHEMA,
    )

    # 2. 删除 declaration 字段
    op.drop_column("plugin_definitions", "declaration", schema=MODULE_SCHEMA)
