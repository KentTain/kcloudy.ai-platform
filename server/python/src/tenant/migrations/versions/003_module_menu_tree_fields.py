"""为 module_menus 表添加树形字段

Revision ID: 003_module_menu_tree_fields
Revises: 002_global_roles
Create Date: 2024-01-21 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_module_menu_tree_fields"
down_revision: Union[str, None] = "002_global_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    """添加树形字段到 module_menus 表"""
    # 0. 删除外键约束（TreeNodeMixin 使用虚拟根节点 "root"）
    op.drop_constraint(
        "module_menus_parent_id_fkey",
        "module_menus",
        schema=MODULE_SCHEMA,
        type_="foreignkey",
    )

    # 1. 添加树形字段
    op.add_column(
        "module_menus",
        sa.Column("tree_leaf", sa.Boolean, nullable=False, server_default="true", comment="是否为叶子节点"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "module_menus",
        sa.Column("tree_level", sa.Integer, nullable=False, server_default="0", comment="树层级"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "module_menus",
        sa.Column("tree_sort", sa.Integer, nullable=False, server_default="0", comment="排序号"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "module_menus",
        sa.Column("tree_sorts", sa.String(512), nullable=False, server_default="", comment="排序路径"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "module_menus",
        sa.Column("tree_names", sa.String(512), nullable=False, server_default="", comment="名称路径"),
        schema=MODULE_SCHEMA,
    )
    op.add_column(
        "module_menus",
        sa.Column("parent_ids", sa.String(1024), nullable=False, server_default="root,", comment="父ID路径"),
        schema=MODULE_SCHEMA,
    )

    # 2. 创建索引
    op.create_index("ix_module_menus_tree_level", "module_menus", ["tree_level"], schema=MODULE_SCHEMA)
    op.create_index("ix_module_menus_tree_sort", "module_menus", ["tree_sort"], schema=MODULE_SCHEMA)

    # 3. 迁移数据：将 sort_order 复制到 tree_sort
    op.execute(
        sa.text(f"""
            UPDATE {MODULE_SCHEMA}.module_menus
            SET tree_sort = sort_order
        """)
    )

    # 4. 删除 sort_order 字段
    op.drop_column("module_menus", "sort_order", schema=MODULE_SCHEMA)


def downgrade() -> None:
    """回滚树形字段"""
    # 1. 重新添加 sort_order 字段
    op.add_column(
        "module_menus",
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0", comment="排序号"),
        schema=MODULE_SCHEMA,
    )

    # 2. 迁移数据：将 tree_sort 复制回 sort_order
    op.execute(
        sa.text(f"""
            UPDATE {MODULE_SCHEMA}.module_menus
            SET sort_order = tree_sort
        """)
    )

    # 3. 删除树形字段
    op.drop_index("ix_module_menus_tree_sort", "module_menus", schema=MODULE_SCHEMA)
    op.drop_index("ix_module_menus_tree_level", "module_menus", schema=MODULE_SCHEMA)
    op.drop_column("module_menus", "parent_ids", schema=MODULE_SCHEMA)
    op.drop_column("module_menus", "tree_names", schema=MODULE_SCHEMA)
    op.drop_column("module_menus", "tree_sorts", schema=MODULE_SCHEMA)
    op.drop_column("module_menus", "tree_sort", schema=MODULE_SCHEMA)
    op.drop_column("module_menus", "tree_level", schema=MODULE_SCHEMA)
    op.drop_column("module_menus", "tree_leaf", schema=MODULE_SCHEMA)

    # 4. 重新创建外键约束
    op.create_foreign_key(
        "module_menus_parent_id_fkey",
        "module_menus",
        "module_menus",
        ["parent_id"],
        ["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema=MODULE_SCHEMA,
        ondelete="SET NULL",
    )
