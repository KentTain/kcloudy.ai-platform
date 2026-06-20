"""AI 模块初始数据库模式

Revision ID: 001_ai_initial
Revises:
Create Date: 2026-06-20

合并原 001~005 迁移的最终状态，创建所有 ai schema 下的表。
本迁移是破坏性重建，不保留历史数据。

包含：
- 插件系统表（plugins, plugin_declarations, plugin_installations, plugin_install_tasks, plugin_credentials）
- 模型提供者表（model_providers, model_configs）
- 对话表（conversations, messages）
- 同 schema 内外键和跨 schema 外键

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_ai_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "ai"


def upgrade() -> None:
    # 创建 ai schema
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # ==================== 插件系统表 ====================

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

    # ==================== 模型提供者表 ====================

    # 创建 model_providers 表（租户隔离）
    op.create_table(
        "model_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("provider_name", sa.String(255), nullable=False, comment="提供商名称"),
        sa.Column("provider_type", sa.String(64), nullable=False, comment="提供商类型"),
        sa.Column("plugin_id", sa.String(128), nullable=True, comment="关联的插件ID"),
        sa.Column("credentials", postgresql.JSONB, nullable=True, comment="凭证配置"),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default="true", comment="是否有效"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_model_providers_tenant_id", "model_providers", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_model_providers_plugin_id", "model_providers", ["plugin_id"], schema=MODULE_SCHEMA)

    # 创建 model_configs 表（租户隔离）
    op.create_table(
        "model_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("provider_id", sa.String(36), nullable=False, comment="关联的模型提供商ID"),
        sa.Column("model_name", sa.String(255), nullable=False, comment="模型名称"),
        sa.Column("model_type", sa.String(32), nullable=False, comment="模型类型"),
        sa.Column("parameters", postgresql.JSONB, nullable=True, comment="默认参数配置"),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default="true", comment="是否有效"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_model_configs_tenant_id", "model_configs", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_model_configs_provider_id", "model_configs", ["provider_id"], schema=MODULE_SCHEMA)

    # 创建 conversations 表（租户隔离）
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("app_id", sa.String(36), nullable=False, comment="应用id"),
        sa.Column("name", sa.String(255), nullable=False, comment="会话名称"),
        sa.Column("status", sa.String(20), nullable=False, server_default="normal", comment="状态"),
        sa.Column("mode", sa.String(20), nullable=False, server_default="chat", comment="会话模式"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_conversations_tenant_id", "conversations", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_conversations_app_id", "conversations", ["app_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_conversations_status", "conversations", ["status"], schema=MODULE_SCHEMA)
    op.create_index("ix_conversations_tenant_app_status", "conversations", ["tenant_id", "app_id", "status"], schema=MODULE_SCHEMA)

    # 创建 messages 表（租户隔离）
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("app_id", sa.String(36), nullable=False, comment="应用id"),
        sa.Column("conversation_id", sa.String(36), nullable=False, comment="会话id"),
        sa.Column("role", sa.String(20), nullable=False, comment="角色"),
        sa.Column("content", sa.Text, nullable=True, comment="消息内容"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", comment="状态"),
        sa.Column("query", sa.Text, nullable=True, comment="用户问题"),
        sa.Column("answer", sa.Text, nullable=True, comment="助手回复"),
        sa.Column("message_metadata", postgresql.JSONB, nullable=True, comment="扩展元数据"),
        sa.Column("token_count", sa.Integer, nullable=True, server_default="0", comment="token数量"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_messages_tenant_id", "messages", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_messages_app_id", "messages", ["app_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_messages_status", "messages", ["status"], schema=MODULE_SCHEMA)
    op.create_index("ix_messages_conv_created", "messages", ["conversation_id", "created_at"], schema=MODULE_SCHEMA)

    # ==================== 同 schema 内外键 ====================

    # model_configs.provider_id -> model_providers.id
    op.create_foreign_key(
        constraint_name="fk_model_configs_provider_id",
        source_table="model_configs",
        referent_table="model_providers",
        local_cols=["provider_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema=MODULE_SCHEMA,
        ondelete="CASCADE",
    )

    # messages.conversation_id -> conversations.id
    op.create_foreign_key(
        constraint_name="fk_messages_conversation_id",
        source_table="messages",
        referent_table="conversations",
        local_cols=["conversation_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema=MODULE_SCHEMA,
        ondelete="CASCADE",
    )

    # ==================== 跨 schema 外键 ====================

    # plugin_installations -> tenant.tenants
    op.create_foreign_key(
        constraint_name="fk_plugin_installations_tenant_id",
        source_table="plugin_installations",
        referent_table="tenants",
        local_cols=["tenant_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="tenant",
        ondelete="CASCADE",
    )

    # plugin_installations -> iam.users
    op.create_foreign_key(
        constraint_name="fk_plugin_installations_created_by",
        source_table="plugin_installations",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        constraint_name="fk_plugin_installations_updated_by",
        source_table="plugin_installations",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugin_install_tasks -> tenant.tenants
    op.create_foreign_key(
        constraint_name="fk_plugin_install_tasks_tenant_id",
        source_table="plugin_install_tasks",
        referent_table="tenants",
        local_cols=["tenant_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="tenant",
        ondelete="CASCADE",
    )

    # plugin_install_tasks -> iam.users
    op.create_foreign_key(
        constraint_name="fk_plugin_install_tasks_created_by",
        source_table="plugin_install_tasks",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        constraint_name="fk_plugin_install_tasks_updated_by",
        source_table="plugin_install_tasks",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugin_credentials -> tenant.tenants
    op.create_foreign_key(
        constraint_name="fk_plugin_credentials_tenant_id",
        source_table="plugin_credentials",
        referent_table="tenants",
        local_cols=["tenant_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="tenant",
        ondelete="CASCADE",
    )

    # plugin_credentials -> iam.users
    op.create_foreign_key(
        constraint_name="fk_plugin_credentials_created_by",
        source_table="plugin_credentials",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        constraint_name="fk_plugin_credentials_updated_by",
        source_table="plugin_credentials",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugins -> iam.users
    op.create_foreign_key(
        constraint_name="fk_plugins_created_by",
        source_table="plugins",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        constraint_name="fk_plugins_updated_by",
        source_table="plugins",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugin_declarations -> iam.users
    op.create_foreign_key(
        constraint_name="fk_plugin_declarations_created_by",
        source_table="plugin_declarations",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        constraint_name="fk_plugin_declarations_updated_by",
        source_table="plugin_declarations",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # model_providers -> tenant.tenants
    op.create_foreign_key(
        constraint_name="fk_model_providers_tenant_id",
        source_table="model_providers",
        referent_table="tenants",
        local_cols=["tenant_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="tenant",
        ondelete="CASCADE",
    )

    # model_providers -> iam.users
    op.create_foreign_key(
        constraint_name="fk_model_providers_created_by",
        source_table="model_providers",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        constraint_name="fk_model_providers_updated_by",
        source_table="model_providers",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # model_configs -> tenant.tenants
    op.create_foreign_key(
        constraint_name="fk_model_configs_tenant_id",
        source_table="model_configs",
        referent_table="tenants",
        local_cols=["tenant_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="tenant",
        ondelete="CASCADE",
    )

    # model_configs -> iam.users
    op.create_foreign_key(
        constraint_name="fk_model_configs_created_by",
        source_table="model_configs",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        constraint_name="fk_model_configs_updated_by",
        source_table="model_configs",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # 删除所有表和 schema（CASCADE 自动处理依赖顺序）
    op.execute(f"DROP SCHEMA IF EXISTS {MODULE_SCHEMA} CASCADE")
