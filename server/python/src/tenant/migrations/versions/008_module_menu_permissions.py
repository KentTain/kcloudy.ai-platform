"""创建 module_menu_permissions 关联表

Revision ID: 008_module_menu_permissions
Revises: 007_menu_paths_resources
Create Date: 2026-06-18

创建菜单与权限的关联表，支持菜单级别权限控制。

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "008_module_menu_permissions"
down_revision: Union[str, None] = "007_menu_paths_resources"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    """创建 module_menu_permissions 表"""

    op.create_table(
        "module_menu_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "module_menu_id",
            sa.String(36),
            sa.ForeignKey(f"{MODULE_SCHEMA}.module_menus.id", ondelete="CASCADE"),
            nullable=False,
            comment="模块菜单ID",
        ),
        sa.Column(
            "module_permission_id",
            sa.String(36),
            sa.ForeignKey(f"{MODULE_SCHEMA}.module_permissions.id", ondelete="CASCADE"),
            nullable=False,
            comment="模块权限ID",
        ),
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
            onupdate=sa.func.now(),
            nullable=False,
            comment="更新时间",
        ),
        schema=MODULE_SCHEMA,
    )

    # 唯一性约束：菜单ID + 权限ID
    op.create_unique_constraint(
        "uq_module_menu_permissions_menu_perm",
        "module_menu_permissions",
        ["module_menu_id", "module_permission_id"],
        schema=MODULE_SCHEMA,
    )

    # 索引
    op.create_index(
        "ix_module_menu_permissions_menu_id",
        "module_menu_permissions",
        ["module_menu_id"],
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "ix_module_menu_permissions_permission_id",
        "module_menu_permissions",
        ["module_permission_id"],
        schema=MODULE_SCHEMA,
    )


def downgrade() -> None:
    """删除 module_menu_permissions 表"""

    op.drop_index(
        "ix_module_menu_permissions_permission_id",
        table_name="module_menu_permissions",
        schema=MODULE_SCHEMA,
    )
    op.drop_index(
        "ix_module_menu_permissions_menu_id",
        table_name="module_menu_permissions",
        schema=MODULE_SCHEMA,
    )
    op.drop_table("module_menu_permissions", schema=MODULE_SCHEMA)
