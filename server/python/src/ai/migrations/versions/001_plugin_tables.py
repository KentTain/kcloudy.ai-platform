"""add plugin tables

Revision ID: 001_plugin
Revises:
Create Date: 2026-06-02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_plugin"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "ai"


def upgrade() -> None:
    # 创建 ai schema
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # 创建 plugins 表（全局，不分租户）
    op.create_table(
        "plugins",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column("plugin_unique_identifier", sa.String(256), nullable=False, unique=True, comment="插件唯一标识符"),
        sa.Column("refers", sa.Integer, nullable=False, server_default="0", comment="引用计数"),
        sa.Column("install_type", sa.String(16), nullable=False, comment="安装类型"),
        sa.Column("manifest_type", sa.String(32), nullable=True, comment="清单类型"),
        sa.Column("remote_declaration", postgresql.JSONB, nullable=True, comment="远程声明"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_plugins_plugin_id", "plugins", ["plugin_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_plugins_install_type", "plugins", ["install_type"], schema=MODULE_SCHEMA)

    # 创建 plugin_declarations 表（全局，不分租户）
    op.create_table(
        "plugin_declarations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column("plugin_unique_identifier", sa.String(256), nullable=False, unique=True, comment="插件唯一标识符"),
        sa.Column("declaration", postgresql.JSONB, nullable=False, comment="声明内容"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_plugin_declarations_plugin_id", "plugin_declarations", ["plugin_id"], schema=MODULE_SCHEMA)

    # 创建 plugin_installations 表（租户隔离）
    op.create_table(
        "plugin_installations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column("plugin_unique_identifier", sa.String(256), nullable=False, comment="插件唯一标识符"),
        sa.Column("runtime_type", sa.String(16), nullable=False, comment="运行时类型"),
        sa.Column("plugin_type", sa.String(16), nullable=False, comment="插件类型"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active", comment="插件运行状态"),
        # 生命周期时间戳
        sa.Column("installed_at", sa.DateTime, nullable=True, comment="安装完成时间"),
        sa.Column("last_started_at", sa.DateTime, nullable=True, comment="最后启动时间"),
        sa.Column("last_stopped_at", sa.DateTime, nullable=True, comment="最后停止时间"),
        sa.Column("last_accessed_at", sa.DateTime, nullable=True, comment="最后访问时间"),
        sa.Column("frozen_at", sa.DateTime, nullable=True, comment="冻结时间"),
        # 运行时信息
        sa.Column("process_id", sa.Integer, nullable=True, comment="进程ID"),
        sa.Column("port", sa.Integer, nullable=True, comment="运行端口"),
        sa.Column("work_directory", sa.String(512), nullable=True, comment="工作目录路径"),
        # 性能和健康状态
        sa.Column("call_count", sa.Integer, nullable=False, server_default="0", comment="调用次数统计"),
        sa.Column("error_count", sa.Integer, nullable=False, server_default="0", comment="错误次数统计"),
        sa.Column("last_error", sa.Text, nullable=True, comment="最后错误信息"),
        sa.Column("health_check_at", sa.DateTime, nullable=True, comment="最后健康检查时间"),
        # 安装配置信息
        sa.Column("install_config", postgresql.JSONB, nullable=True, comment="安装配置信息"),
        sa.Column("runtime_config", postgresql.JSONB, nullable=True, comment="运行时配置信息"),
        # 自动管理配置
        sa.Column("auto_start", sa.Boolean, nullable=False, server_default="false", comment="是否自动启动"),
        sa.Column("freeze_threshold_hours", sa.Integer, nullable=False, server_default="24", comment="冻结阈值（小时）"),
        sa.Column("endpoints_setups", sa.Integer, nullable=False, server_default="0", comment="端点设置数"),
        sa.Column("endpoints_active", sa.Integer, nullable=False, server_default="0", comment="活跃端点数"),
        sa.Column("source", sa.String(16), nullable=True, comment="来源"),
        sa.Column("meta", postgresql.JSONB, nullable=True, comment="元数据"),
        sa.Column("plugin_config", postgresql.JSONB, nullable=True, comment="插件配置"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_plugin_installations_tenant_id", "plugin_installations", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_plugin_installations_plugin_id", "plugin_installations", ["plugin_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_plugin_installations_plugin_unique_identifier", "plugin_installations", ["plugin_unique_identifier"], schema=MODULE_SCHEMA)

    # 创建 plugin_install_tasks 表（租户隔离）
    op.create_table(
        "plugin_install_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("status", sa.String(16), nullable=False, comment="状态"),
        sa.Column("total_plugins", sa.Integer, nullable=False, comment="总插件数"),
        sa.Column("completed_plugins", sa.Integer, nullable=False, comment="已完成插件数"),
        sa.Column("plugins", postgresql.JSONB, nullable=True, comment="插件状态列表"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_plugin_install_tasks_tenant_id", "plugin_install_tasks", ["tenant_id"], schema=MODULE_SCHEMA)

    # 创建 plugin_credentials 表（租户隔离）
    op.create_table(
        "plugin_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column("plugin_type", sa.String(16), nullable=False, comment="插件类型"),
        sa.Column("scope", sa.String(16), nullable=False, server_default="global", comment="凭证作用域"),
        sa.Column("name", sa.String(128), nullable=False, comment="凭证名称"),
        sa.Column("provider_name", sa.String(128), nullable=True, comment="工具提供者名"),
        sa.Column("credentials", postgresql.JSONB, nullable=False, comment="凭证JSON"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_plugin_credentials_tenant_id", "plugin_credentials", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_plugin_credentials_plugin_id", "plugin_credentials", ["plugin_id"], schema=MODULE_SCHEMA)


def downgrade() -> None:
    op.drop_table("plugin_credentials", schema=MODULE_SCHEMA)
    op.drop_table("plugin_install_tasks", schema=MODULE_SCHEMA)
    op.drop_table("plugin_installations", schema=MODULE_SCHEMA)
    op.drop_table("plugin_declarations", schema=MODULE_SCHEMA)
    op.drop_table("plugins", schema=MODULE_SCHEMA)
    op.execute(f"DROP SCHEMA IF EXISTS {MODULE_SCHEMA} CASCADE")
