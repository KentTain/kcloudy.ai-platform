"""新增 Skill 支持字段到 plugin_definitions 表

Revision ID: 003_add_skill_support
Revises: 002_add_installed_at
Create Date: 2026-07-06

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_add_skill_support"
down_revision: str | None = "002_add_installed_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    """扩展 plugin_definitions 表，新增 Skill 特有字段"""
    # 新增 skill_type 字段
    op.add_column(
        "plugin_definitions",
        sa.Column(
            "skill_type",
            sa.String(16),
            nullable=True,
            comment="Skill 类型：knowledge(知识文档) | script(简单脚本)",
        ),
        schema=MODULE_SCHEMA,
    )

    # 新增 runtime_type 字段
    op.add_column(
        "plugin_definitions",
        sa.Column(
            "runtime_type",
            sa.String(16),
            nullable=True,
            comment="运行时类型：none(零隔离) | sandbox(轻量级沙箱) | local(本地进程)",
        ),
        schema=MODULE_SCHEMA,
    )

    # 添加部分索引，仅对 skill 类型查询优化
    # 注意：plugin_type 字段存在于 plugin_installations 表，而非 plugin_definitions 表
    # 此处为 skill_type 字段创建索引以优化按技能类型查询
    op.create_index(
        "idx_plugin_definitions_skill_type",
        "plugin_definitions",
        ["skill_type"],
        schema=MODULE_SCHEMA,
        postgresql_where=sa.text("skill_type IS NOT NULL"),
    )


def downgrade() -> None:
    """移除 Skill 支持字段"""
    op.drop_index("idx_plugin_definitions_skill_type", table_name="plugin_definitions", schema=MODULE_SCHEMA)
    op.drop_column("plugin_definitions", "runtime_type", schema=MODULE_SCHEMA)
    op.drop_column("plugin_definitions", "skill_type", schema=MODULE_SCHEMA)
