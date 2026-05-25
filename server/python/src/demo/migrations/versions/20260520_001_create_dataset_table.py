"""create dataset table

Revision ID: demo_001_create_dataset
Revises:
Create Date: 2026-05-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "demo_001_create_dataset"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dataset",
        sa.Column("id", sa.String(36), primary_key=True, comment="主键ID"),
        sa.Column("name", sa.String(255), nullable=False, comment="知识库名称"),
        sa.Column("description", sa.Text, nullable=True, comment="知识库描述"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
    )


def downgrade() -> None:
    op.drop_table("dataset")