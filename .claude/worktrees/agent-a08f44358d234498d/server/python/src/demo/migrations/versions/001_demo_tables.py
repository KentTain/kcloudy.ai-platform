"""add demo tables

Revision ID: 001_demo
Revises:
Create Date: 2026-05-29

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_demo"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 模块 schema
MODULE_SCHEMA = "demo"


def upgrade() -> None:
    # 创建 demo schema
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # 创建 dataset 表
    op.create_table(
        "dataset",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenant.tenants.id", ondelete="CASCADE"),
            nullable=False,
            comment="租户ID",
        ),
        sa.Column("name", sa.String(255), nullable=False, comment="知识库名称"),
        sa.Column("description", sa.Text, nullable=True, comment="知识库描述"),
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
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_dataset_tenant_id", "dataset", ["tenant_id"], schema=MODULE_SCHEMA
    )


def downgrade() -> None:
    op.drop_table("dataset", schema=MODULE_SCHEMA)
    op.execute(f"DROP SCHEMA IF EXISTS {MODULE_SCHEMA} CASCADE")
