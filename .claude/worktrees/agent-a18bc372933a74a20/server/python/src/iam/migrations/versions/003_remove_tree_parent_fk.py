"""remove parent_id foreign key constraints from tree tables

Revision ID: 003_remove_tree_parent_fk
Revises: 002_iam_tenant_isolation
Create Date: 2026-06-02

移除 departments 和 menus 表的 parent_id 外键约束。

原因：
- TreeNodeMixin 使用虚拟根节点设计，顶级节点的 parent_id 为 "root"
- 数据库中不存在 id="root" 的记录，外键约束会导致插入失败
- 树结构的父子关系通过 parent_ids 字段维护，应用层保证一致性

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_remove_tree_parent_fk"
down_revision: Union[str, None] = "002_iam_tenant_isolation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 模块 schema
MODULE_SCHEMA = "iam"


def upgrade() -> None:
    """移除 parent_id 外键约束"""

    # 1. 移除 departments 表的 parent_id 外键约束
    op.drop_constraint(
        constraint_name="departments_parent_id_fkey",
        table_name="departments",
        schema=MODULE_SCHEMA,
        type_="foreignkey",
    )

    # 2. 移除 menus 表的 parent_id 外键约束
    op.drop_constraint(
        constraint_name="menus_parent_id_fkey",
        table_name="menus",
        schema=MODULE_SCHEMA,
        type_="foreignkey",
    )


def downgrade() -> None:
    """恢复 parent_id 外键约束"""

    # 1. 恢复 departments 表的 parent_id 外键约束
    op.create_foreign_key(
        constraint_name="departments_parent_id_fkey",
        source_table="departments",
        referent_table="departments",
        local_cols=["parent_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema=MODULE_SCHEMA,
        ondelete="SET NULL",
    )

    # 2. 恢复 menus 表的 parent_id 外键约束
    op.create_foreign_key(
        constraint_name="menus_parent_id_fkey",
        source_table="menus",
        referent_table="menus",
        local_cols=["parent_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema=MODULE_SCHEMA,
        ondelete="SET NULL",
    )
