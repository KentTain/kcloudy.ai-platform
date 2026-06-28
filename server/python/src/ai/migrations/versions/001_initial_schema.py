"""AI 模块初始数据库模式

Revision ID: 001_ai_initial
Revises:
Create Date: 2026-06-20
Update Date: 2026-06-25

架构变更（2026-06-25）：
- 移除 plugins、plugin_declarations、plugin_installations 表的创建
- 这些表已迁移至 Tenant 模块（tenant.plugin_definitions、tenant.plugin_installations）
- AI 模块保留：plugin_install_tasks、plugin_credentials

当前包含：
- 插件系统表（plugin_install_tasks、plugin_credentials）
- 模型提供者表（model_providers、model_configs）
- 对话表（conversations、messages）
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

    # 创建 plugin_install_tasks 表（插件安装任务）
    op.create_table(
        "plugin_install_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("status", sa.String(16), nullable=False, comment="状态，running, success, failed"),
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

    # 创建 plugin_credentials 表（插件凭证）
    op.create_table(
        "plugin_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column("plugin_type", sa.String(16), nullable=False, comment="插件类型"),
        sa.Column("scope", sa.String(16), nullable=False, server_default="global", comment="作用域"),
        sa.Column("name", sa.String(64), nullable=False, comment="凭证名称"),
        sa.Column("credentials", postgresql.JSONB, nullable=False, comment="凭证内容"),
        sa.Column("is_disabled", sa.Boolean, nullable=False, server_default="false", comment="是否禁用"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_plugin_credentials_tenant_name"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_plugin_credentials_tenant_id", "plugin_credentials", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_plugin_credentials_plugin_id", "plugin_credentials", ["plugin_id"], schema=MODULE_SCHEMA)

    # ==================== 模型提供者表 ====================

    # 创建 model_providers 表
    op.create_table(
        "model_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("provider_type", sa.String(64), nullable=False, comment="提供商类型"),
        sa.Column("provider_name", sa.String(128), nullable=False, comment="提供商名称"),
        sa.Column("icon", sa.String(256), nullable=True, comment="图标URL"),
        sa.Column("description", sa.Text, nullable=True, comment="描述"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_model_providers_tenant_id", "model_providers", ["tenant_id"], schema=MODULE_SCHEMA)

    # 创建 model_configs 表
    op.create_table(
        "model_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("provider_id", sa.String(36), nullable=False, comment="提供商ID"),
        sa.Column("model_type", sa.String(32), nullable=False, comment="模型类型"),
        sa.Column("model_name", sa.String(128), nullable=False, comment="模型名称"),
        sa.Column("config", postgresql.JSONB, nullable=True, comment="模型配置"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_model_configs_tenant_id", "model_configs", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_model_configs_provider_id", "model_configs", ["provider_id"], schema=MODULE_SCHEMA)

    # ==================== 对话表 ====================

    # 创建 conversations 表
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("user_id", sa.String(36), nullable=False, comment="用户ID"),
        sa.Column("mode", sa.String(32), nullable=False, server_default="chat", comment="对话模式"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active", comment="对话状态"),
        sa.Column("title", sa.String(512), nullable=True, comment="对话标题"),
        sa.Column("summary", sa.Text, nullable=True, comment="对话摘要"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_conversations_tenant_id", "conversations", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"], schema=MODULE_SCHEMA)

    # 创建 messages 表
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("conversation_id", sa.String(36), nullable=False, comment="对话ID"),
        sa.Column("parent_message_id", sa.String(36), nullable=True, comment="父消息ID"),
        sa.Column("role", sa.String(32), nullable=False, comment="角色"),
        sa.Column("content", sa.Text, nullable=False, comment="消息内容"),
        sa.Column("status", sa.String(32), nullable=False, server_default="success", comment="消息状态"),
        sa.Column("error", sa.Text, nullable=True, comment="错误信息"),
        sa.Column("metadata", postgresql.JSONB, nullable=True, comment="元数据"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_messages_tenant_id", "messages", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], schema=MODULE_SCHEMA)

    # ==================== 跨 Schema 外键 ====================
    # 注意：跨 schema 外键需要在两个 schema 都创建后才能创建
    # 这里我们创建指向 iam.users 的外键（如果 iam schema 已存在）

    # messages 表的 user_id 外键（指向 iam.users）
    # 使用 PL/pgSQL 块处理，避免 DDL 失败导致 PostgreSQL 事务中止
    # 如果 iam schema 不存在或 iam.users 表不存在，外键创建会被跳过
    op.execute(f"""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.schemata WHERE schema_name = 'iam'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'iam' AND table_name = 'users'
        ) THEN
            ALTER TABLE {MODULE_SCHEMA}.messages
                ADD CONSTRAINT fk_messages_user_id
                FOREIGN KEY (tenant_id, user_id)
                REFERENCES iam.users(tenant_id, id);
        END IF;
    EXCEPTION WHEN OTHERS THEN
        NULL;
    END $$;
    """)


def downgrade() -> None:
    # 按依赖顺序逆序删除表
    op.drop_table("messages", schema=MODULE_SCHEMA)
    op.drop_table("conversations", schema=MODULE_SCHEMA)
    op.drop_table("model_configs", schema=MODULE_SCHEMA)
    op.drop_table("model_providers", schema=MODULE_SCHEMA)
    op.drop_table("plugin_credentials", schema=MODULE_SCHEMA)
    op.drop_table("plugin_install_tasks", schema=MODULE_SCHEMA)
