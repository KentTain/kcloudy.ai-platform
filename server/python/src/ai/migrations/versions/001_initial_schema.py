"""AI 模块初始数据库模式

Revision ID: 001_ai_initial
Revises:
Create Date: 2026-06-28

合并所有迁移的最终状态，创建所有 ai schema 下的表。
本迁移是破坏性重建，不保留历史数据。

当前包含：
- 插件系统表（plugin_install_tasks、plugin_credentials、plugin_configs、plugin_runtime_states）
- 模型提供者表（model_providers、model_configs）
- 对话表（conversations、messages）
- 同 schema 内外键

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

    # ==================== 会话表 ====================

    op.create_table(
        "conversations",
        sa.Column("app_id", sa.String(36), nullable=False, comment="应用id"),
        sa.Column("name", sa.String(255), nullable=False, comment="会话名称"),
        sa.Column("status", sa.String(64), nullable=False, comment="状态"),
        sa.Column("mode", sa.String(64), nullable=False, comment="会话模式"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
        comment="会话",
    )
    op.create_index(op.f("ix_ai_conversations_app_id"), "conversations", ["app_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_ai_conversations_tenant_id"), "conversations", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 模型提供者表 ====================

    op.create_table(
        "model_providers",
        sa.Column("provider_name", sa.String(255), nullable=False, comment="提供商名称，如 openai、anthropic"),
        sa.Column("provider_type", sa.String(64), nullable=False, comment="提供商类型，如 openai、anthropic、azure、custom"),
        sa.Column("plugin_id", sa.String(128), nullable=True, comment="关联的插件ID，manifest中的author+name"),
        sa.Column("credentials", postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="凭证配置（加密存储），包含API密钥等敏感信息"),
        sa.Column("is_valid", sa.Boolean(), nullable=False, comment="是否有效，用于软删除或禁用"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(op.f("ix_ai_model_providers_plugin_id"), "model_providers", ["plugin_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_ai_model_providers_tenant_id"), "model_providers", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 插件配置表 ====================

    op.create_table(
        "plugin_configs",
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column("plugin_unique_identifier", sa.String(256), nullable=False, comment="插件唯一标识符"),
        sa.Column("plugin_config", postgresql.JSON(astext_type=sa.Text()), nullable=True, comment="插件能力定义和持久化配置"),
        sa.Column("runtime_config", postgresql.JSON(astext_type=sa.Text()), nullable=True, comment="运行时配置"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "plugin_id", name="uq_plugin_configs_tenant_plugin"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(op.f("ix_ai_plugin_configs_plugin_id"), "plugin_configs", ["plugin_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_ai_plugin_configs_tenant_id"), "plugin_configs", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 插件凭证表 ====================

    op.create_table(
        "plugin_credentials",
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID，manifest中的author+name，例如alon/tongyi"),
        sa.Column("plugin_type", sa.String(16), nullable=False, comment="插件类型"),
        sa.Column("scope", sa.String(16), nullable=False, comment="作用域，global全局、personal个人"),
        sa.Column("name", sa.String(64), nullable=False, comment="凭证名称，租户级唯一"),
        sa.Column("credentials", sa.JSON(), nullable=False, comment="凭证内容，JSON格式"),
        sa.Column("is_disabled", sa.Boolean(), nullable=False, comment="是否禁用"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_plugin_credentials_tenant_name"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(op.f("ix_ai_plugin_credentials_plugin_id"), "plugin_credentials", ["plugin_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_ai_plugin_credentials_tenant_id"), "plugin_credentials", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 插件安装任务表 ====================

    op.create_table(
        "plugin_install_tasks",
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column("plugin_unique_identifier", sa.String(256), nullable=False, comment="插件唯一标识符"),
        sa.Column("status", sa.String(16), nullable=False, comment="状态: pending, running, completed, failed, timeout"),
        sa.Column("progress", sa.Integer(), nullable=False, comment="进度百分比 (0-100)"),
        sa.Column("current_step", sa.String(64), nullable=True, comment="当前步骤描述"),
        sa.Column("steps", sa.JSON(), nullable=True, comment="步骤列表与状态"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="错误信息"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True, comment="开始时间"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True, comment="完成时间"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(op.f("ix_ai_plugin_install_tasks_plugin_id"), "plugin_install_tasks", ["plugin_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_ai_plugin_install_tasks_tenant_id"), "plugin_install_tasks", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 插件运行时状态表 ====================

    op.create_table(
        "plugin_runtime_states",
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column("status", sa.String(16), nullable=False, comment="运行时状态"),
        sa.Column("process_id", sa.Integer(), nullable=True, comment="进程ID"),
        sa.Column("port", sa.Integer(), nullable=True, comment="运行端口"),
        sa.Column("call_count", sa.Integer(), nullable=False, comment="调用次数统计"),
        sa.Column("error_count", sa.Integer(), nullable=False, comment="错误次数统计"),
        sa.Column("last_error", sa.Text(), nullable=True, comment="最后错误信息"),
        sa.Column("last_started_at", sa.DateTime(), nullable=True, comment="最后启动时间"),
        sa.Column("last_stopped_at", sa.DateTime(), nullable=True, comment="最后停止时间"),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True, comment="最后访问时间"),
        sa.Column("frozen_at", sa.DateTime(), nullable=True, comment="冻结时间"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "plugin_id", name="uq_plugin_runtime_states_tenant_plugin"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(op.f("ix_ai_plugin_runtime_states_plugin_id"), "plugin_runtime_states", ["plugin_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_ai_plugin_runtime_states_tenant_id"), "plugin_runtime_states", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 消息表（依赖 conversations） ====================

    op.create_table(
        "messages",
        sa.Column("app_id", sa.String(36), nullable=False, comment="应用id"),
        sa.Column("conversation_id", sa.String(36), nullable=False, comment="会话id"),
        sa.Column("role", sa.String(64), nullable=False, comment="角色"),
        sa.Column("content", sa.Text(), nullable=True, comment="消息内容"),
        sa.Column("status", sa.String(64), nullable=False, comment="状态"),
        sa.Column("query", sa.Text(), nullable=True, comment="用户问题"),
        sa.Column("answer", sa.Text(), nullable=True, comment="助手回复"),
        sa.Column("message_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="扩展元数据"),
        sa.Column("token_count", sa.Integer(), nullable=True, comment="token数量"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai.conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
        comment="消息",
    )
    op.create_index(op.f("ix_ai_messages_app_id"), "messages", ["app_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_ai_messages_conversation_id"), "messages", ["conversation_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_ai_messages_tenant_id"), "messages", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 模型配置表（依赖 model_providers） ====================

    op.create_table(
        "model_configs",
        sa.Column("provider_id", sa.String(36), nullable=False, comment="关联的模型提供商ID"),
        sa.Column("model_name", sa.String(255), nullable=False, comment="模型名称，如 gpt-4、claude-3-opus"),
        sa.Column("model_type", sa.String(32), nullable=False, comment="模型类型，如 llm、text-embedding、rerank"),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="默认参数配置，如 temperature、max_tokens"),
        sa.Column("is_valid", sa.Boolean(), nullable=False, comment="是否有效，用于软删除或禁用"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.ForeignKeyConstraint(["provider_id"], ["ai.model_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(op.f("ix_ai_model_configs_provider_id"), "model_configs", ["provider_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_ai_model_configs_tenant_id"), "model_configs", ["tenant_id"], schema=MODULE_SCHEMA)


def downgrade() -> None:
    # 删除所有表和 schema（CASCADE 自动处理依赖顺序）
    op.execute(f"DROP SCHEMA IF EXISTS {MODULE_SCHEMA} CASCADE")
