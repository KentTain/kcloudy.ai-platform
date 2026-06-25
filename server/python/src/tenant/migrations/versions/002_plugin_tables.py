"""Tenant 模块插件资源管理表

Revision ID: 002_tenant_plugins
Revises: 001_tenant_initial
Create Date: 2026-06-25

新增插件定义表和租户级插件安装记录表，为插件资源管理架构提供基础设施。

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_tenant_plugins"
down_revision: str | None = "001_tenant_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    # 确保 tenant schema 存在
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # ==================== 插件定义表 ====================
    op.create_table(
        "plugin_definitions",
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("plugin_id", sa.String(length=128), nullable=False, comment="插件ID"),
        sa.Column(
            "plugin_unique_identifier",
            sa.String(length=256),
            nullable=False,
            unique=True,
            comment="插件唯一标识符",
        ),
        sa.Column(
            "refers",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="引用计数",
        ),
        sa.Column(
            "install_type",
            sa.String(length=16),
            nullable=False,
            comment="安装类型",
        ),
        sa.Column(
            "manifest_type",
            sa.String(length=32),
            nullable=True,
            comment="清单类型",
        ),
        sa.Column(
            "remote_declaration",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="远程声明",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column(
            "created_by",
            sa.String(length=36),
            nullable=True,
            comment="创建人",
        ),
        sa.Column(
            "updated_by",
            sa.String(length=36),
            nullable=True,
            comment="更新人",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_definitions_plugin_id",
        "plugin_definitions",
        ["plugin_id"],
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_definitions_install_type",
        "plugin_definitions",
        ["install_type"],
        schema=MODULE_SCHEMA,
    )

    # ==================== 租户级插件安装记录表 ====================
    op.create_table(
        "plugin_installations",
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column(
            "tenant_id",
            sa.String(length=36),
            nullable=False,
            comment="租户ID",
        ),
        sa.Column(
            "plugin_id",
            sa.String(length=128),
            nullable=False,
            comment="插件ID",
        ),
        sa.Column(
            "plugin_unique_identifier",
            sa.String(length=256),
            nullable=False,
            comment="插件唯一标识符",
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'PENDING'"),
            comment="安装状态",
        ),
        sa.Column(
            "auto_start",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否自动启动",
        ),
        sa.Column(
            "freeze_threshold_hours",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("24"),
            comment="冻结阈值（小时）",
        ),
        sa.Column(
            "plugin_type",
            sa.String(length=16),
            nullable=True,
            comment="插件类型",
        ),
        sa.Column(
            "runtime_type",
            sa.String(length=16),
            nullable=True,
            comment="运行时类型",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column(
            "created_by",
            sa.String(length=36),
            nullable=True,
            comment="创建人",
        ),
        sa.Column(
            "updated_by",
            sa.String(length=36),
            nullable=True,
            comment="更新人",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "plugin_id",
            name="ix_plugin_installations_tenant_plugin",
        ),
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_installations_tenant_id",
        "plugin_installations",
        ["tenant_id"],
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_installations_plugin_id",
        "plugin_installations",
        ["plugin_id"],
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_plugin_installations_plugin_unique_identifier",
        "plugin_installations",
        ["plugin_unique_identifier"],
        schema=MODULE_SCHEMA,
    )


def downgrade() -> None:
    # 按依赖顺序逆序删除表
    op.drop_table("plugin_installations", schema=MODULE_SCHEMA)
    op.drop_table("plugin_definitions", schema=MODULE_SCHEMA)
