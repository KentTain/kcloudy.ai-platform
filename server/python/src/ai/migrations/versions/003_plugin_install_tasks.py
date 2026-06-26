"""新增插件安装任务表

Revision ID: 003_plugin_install_tasks
Revises: 002_ai_plugin_configs
Create Date: 2026-06-25

新增 ai.plugin_install_tasks 表，用于异步安装任务追踪。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_plugin_install_tasks"
down_revision: str | None = "002_ai_plugin_configs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "ai"


def upgrade() -> None:
    """升级：创建插件安装任务表"""

    # 确保 ai schema 存在
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # 创建安装任务表
    op.create_table(
        "plugin_install_tasks",
        sa.Column("id", sa.String(64), primary_key=True, comment="任务ID"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column(
            "plugin_unique_identifier",
            sa.String(256),
            nullable=False,
            comment="插件唯一标识符",
        ),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'pending'"),
            comment="状态: pending, running, completed, failed, timeout",
        ),
        sa.Column(
            "progress",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
            comment="进度百分比 (0-100)",
        ),
        sa.Column(
            "current_step",
            sa.String(64),
            nullable=True,
            comment="当前步骤描述",
        ),
        sa.Column(
            "steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="步骤列表与状态",
        ),
        sa.Column(
            "error_message",
            sa.Text,
            nullable=True,
            comment="错误信息",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="开始时间",
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="完成时间",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column(
            "created_by",
            sa.String(36),
            nullable=True,
            comment="创建人",
        ),
        sa.Column(
            "updated_by",
            sa.String(36),
            nullable=True,
            comment="更新人",
        ),
        schema=MODULE_SCHEMA,
    )

    # 创建索引
    op.create_index(
        "ix_plugin_install_tasks_tenant_id",
        "plugin_install_tasks",
        ["tenant_id"],
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_install_tasks_plugin_id",
        "plugin_install_tasks",
        ["plugin_id"],
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_install_tasks_status",
        "plugin_install_tasks",
        ["status"],
        schema=MODULE_SCHEMA,
    )


def downgrade() -> None:
    """回滚：删除插件安装任务表"""

    op.drop_table("plugin_install_tasks", schema=MODULE_SCHEMA)
