"""AI 模块插件配置与运行时状态表

Revision ID: 002_ai_plugin_configs
Revises: 001_ai_initial
Create Date: 2026-06-25

新增插件配置表和插件运行时状态表，为插件资源管理架构提供基础设施。

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_ai_plugin_configs"
down_revision: str | None = "001_ai_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "ai"


def upgrade() -> None:
    # 确保 ai schema 存在
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # ==================== 插件配置表（租户隔离） ====================
    op.create_table(
        "plugin_configs",
        sa.Column("id", sa.String(36), primary_key=True, comment="主键ID"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column(
            "plugin_unique_identifier",
            sa.String(256),
            nullable=False,
            comment="插件唯一标识符",
        ),
        sa.Column(
            "plugin_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="插件配置",
        ),
        sa.Column(
            "runtime_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="运行时配置",
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
        sa.UniqueConstraint(
            "tenant_id",
            "plugin_id",
            name="uq_plugin_configs_tenant_plugin",
        ),
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_configs_tenant_id",
        "plugin_configs",
        ["tenant_id"],
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_configs_plugin_id",
        "plugin_configs",
        ["plugin_id"],
        schema=MODULE_SCHEMA,
    )

    # ==================== 运行时状态表（租户隔离） ====================
    op.create_table(
        "plugin_runtime_states",
        sa.Column("id", sa.String(36), primary_key=True, comment="主键ID"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'inactive'"),
            comment="运行时状态",
        ),
        sa.Column(
            "process_id",
            sa.Integer,
            nullable=True,
            comment="进程ID",
        ),
        sa.Column(
            "port",
            sa.Integer,
            nullable=True,
            comment="运行端口",
        ),
        sa.Column(
            "call_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
            comment="调用次数统计",
        ),
        sa.Column(
            "error_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
            comment="错误次数统计",
        ),
        sa.Column(
            "last_error",
            sa.Text,
            nullable=True,
            comment="最后错误信息",
        ),
        sa.Column(
            "last_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="最后启动时间",
        ),
        sa.Column(
            "last_stopped_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="最后停止时间",
        ),
        sa.Column(
            "last_accessed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="最后访问时间",
        ),
        sa.Column(
            "frozen_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="冻结时间",
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
        sa.UniqueConstraint(
            "tenant_id",
            "plugin_id",
            name="uq_plugin_runtime_states_tenant_plugin",
        ),
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_runtime_states_tenant_id",
        "plugin_runtime_states",
        ["tenant_id"],
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_runtime_states_plugin_id",
        "plugin_runtime_states",
        ["plugin_id"],
        schema=MODULE_SCHEMA,
    )


def downgrade() -> None:
    # 按依赖顺序逆序删除表
    op.drop_table("plugin_runtime_states", schema=MODULE_SCHEMA)
    op.drop_table("plugin_configs", schema=MODULE_SCHEMA)
