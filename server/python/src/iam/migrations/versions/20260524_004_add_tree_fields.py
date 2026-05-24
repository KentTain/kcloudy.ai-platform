"""add tree fields to departments

Revision ID: 004_tree
Revises: 003_tenant_resource
Create Date: 2026-05-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_tree"
down_revision: Union[str, None] = "003_tenant_resource"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加树字段到 departments 表
    op.add_column("departments", sa.Column("tree_leaf", sa.Boolean, nullable=False, server_default="true", comment="是否为叶子节点"))
    op.add_column("departments", sa.Column("tree_level", sa.Integer, nullable=False, server_default="0", comment="树层级"))
    op.add_column("departments", sa.Column("tree_sort", sa.Integer, nullable=False, server_default="0", comment="排序号"))
    op.add_column("departments", sa.Column("tree_sorts", sa.String(512), nullable=False, server_default="", comment="排序路径"))
    op.add_column("departments", sa.Column("tree_names", sa.String(512), nullable=False, server_default="", comment="名称路径"))
    op.add_column("departments", sa.Column("parent_ids", sa.String(512), nullable=False, server_default="root,", comment="父ID路径"))

    # 添加索引
    op.create_index("ix_departments_tree_sorts", "departments", ["tree_sorts"])


def downgrade() -> None:
    # 移除索引
    op.drop_index("ix_departments_tree_sorts", table_name="departments")

    # 移除树字段
    op.drop_column("departments", "parent_ids")
    op.drop_column("departments", "tree_names")
    op.drop_column("departments", "tree_sorts")
    op.drop_column("departments", "tree_sort")
    op.drop_column("departments", "tree_level")
    op.drop_column("departments", "tree_leaf")