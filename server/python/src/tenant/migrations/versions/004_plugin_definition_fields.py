"""新增 plugin_definitions 字段：is_recommended、is_enabled

Revision ID: 004_plugin_definition_fields
Revises: 003_add_declaration_field
Create Date: 2026-06-25

新增插件定义管理所需字段：
- is_recommended: 是否推荐
- is_enabled: 是否启用
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_plugin_definition_fields"
down_revision: str | None = "003_add_declaration_field"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    """升级：添加 is_recommended 和 is_enabled 字段"""

    # 添加 is_recommended 字段
    op.add_column(
        "plugin_definitions",
        sa.Column(
            "is_recommended",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否推荐",
        ),
        schema=MODULE_SCHEMA,
    )

    # 添加 is_enabled 字段
    op.add_column(
        "plugin_definitions",
        sa.Column(
            "is_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否启用",
        ),
        schema=MODULE_SCHEMA,
    )


def downgrade() -> None:
    """回滚：删除 is_recommended 和 is_enabled 字段"""

    op.drop_column("plugin_definitions", "is_enabled", schema=MODULE_SCHEMA)
    op.drop_column("plugin_definitions", "is_recommended", schema=MODULE_SCHEMA)
