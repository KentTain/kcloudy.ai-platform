"""add conversation and message tables

Revision ID: 005_conversation
Revises: 004_model_provider_fks
Create Date: 2026-06-03

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_conversation"
down_revision: str | None = "004_model_provider_fks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "ai"


def upgrade() -> None:
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
    # 复合索引：按租户+应用+状态组合过滤
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
    # 复合索引：按会话查询消息并按时间排序
    op.create_index("ix_messages_conv_created", "messages", ["conversation_id", "created_at"], schema=MODULE_SCHEMA)

    # 同 schema 内外键：messages.conversation_id -> conversations.id
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


def downgrade() -> None:
    # 删除外键
    op.drop_constraint("fk_messages_conversation_id", "messages", schema=MODULE_SCHEMA, type_="foreignkey")

    # 删除表
    op.drop_index("ix_messages_conv_created", "messages", schema=MODULE_SCHEMA)
    op.drop_index("ix_messages_status", "messages", schema=MODULE_SCHEMA)
    op.drop_table("messages", schema=MODULE_SCHEMA)
    op.drop_index("ix_conversations_tenant_app_status", "conversations", schema=MODULE_SCHEMA)
    op.drop_table("conversations", schema=MODULE_SCHEMA)
