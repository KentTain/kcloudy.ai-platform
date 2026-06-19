"""add module sync fields to iam tables

Revision ID: 004_iam_module_sync
Revises: 003_remove_tree_parent_fk
Create Date: 2026-06-09

向 permissions、roles、menus 表新增模块同步相关字段和约束：
- permissions: 新增 tenant_id、ref_id 列，修改唯一约束
- roles: 新增 ref_id 列，新增唯一约束
- menus: 新增 tenant_id、ref_id 列，修改唯一约束
- user_roles: 修改唯一约束，加入 tenant_id
- role_permissions: 修改唯一约束，加入 tenant_id

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_iam_module_sync"
down_revision: str | None = "003_remove_tree_parent_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "iam"


def upgrade() -> None:
    # ==================== permissions 表 ====================

    # 新增 tenant_id 列
    op.add_column(
        "permissions",
        sa.Column("tenant_id", sa.String(36), nullable=True, comment="租户ID（NULL 表示全局权限）"),
        schema=MODULE_SCHEMA,
    )

    # 新增 ref_id 列
    op.add_column(
        "permissions",
        sa.Column("ref_id", sa.String(36), nullable=True, comment="模块定义层关联ID"),
        schema=MODULE_SCHEMA,
    )

    # 删除 code 的 unique constraint（PostgreSQL 自动命名为 {table}_{column}_key）
    op.drop_constraint("permissions_code_key", "permissions", schema=MODULE_SCHEMA, type_="unique")

    # 新增 (tenant_id, code) unique constraint
    op.create_unique_constraint("uq_permissions_tenant_code", "permissions", ["tenant_id", "code"], schema=MODULE_SCHEMA)

    # 新增索引
    op.create_index("ix_permissions_tenant_id", "permissions", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_permissions_ref_id", "permissions", ["ref_id"], schema=MODULE_SCHEMA)

    # ==================== roles 表 ====================

    # 新增 ref_id 列（tenant_id 已在 001_iam 迁移中添加）
    op.add_column(
        "roles",
        sa.Column("ref_id", sa.String(36), nullable=True, comment="模块定义层关联ID"),
        schema=MODULE_SCHEMA,
    )

    # 新增 (tenant_id, code) unique constraint
    op.create_unique_constraint("uq_roles_tenant_code", "roles", ["tenant_id", "code"], schema=MODULE_SCHEMA)

    # 新增索引
    op.create_index("ix_roles_ref_id", "roles", ["ref_id"], schema=MODULE_SCHEMA)

    # ==================== menus 表 ====================

    # 新增 tenant_id 列
    op.add_column(
        "menus",
        sa.Column("tenant_id", sa.String(36), nullable=True, comment="租户ID（NULL 表示全局菜单）"),
        schema=MODULE_SCHEMA,
    )

    # 新增 ref_id 列
    op.add_column(
        "menus",
        sa.Column("ref_id", sa.String(36), nullable=True, comment="模块定义层关联ID"),
        schema=MODULE_SCHEMA,
    )

    # 删除 code 的 unique constraint（PostgreSQL 自动命名为 {table}_{column}_key）
    op.drop_constraint("menus_code_key", "menus", schema=MODULE_SCHEMA, type_="unique")

    # 新增 (tenant_id, code) unique constraint
    op.create_unique_constraint("uq_menus_tenant_code", "menus", ["tenant_id", "code"], schema=MODULE_SCHEMA)

    # 新增索引
    op.create_index("ix_menus_tenant_id", "menus", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_menus_ref_id", "menus", ["ref_id"], schema=MODULE_SCHEMA)

    # ==================== user_roles 表 ====================

    # 修改唯一约束：加入 tenant_id
    op.drop_constraint("uq_user_roles_user_role", "user_roles", schema=MODULE_SCHEMA, type_="unique")
    op.create_unique_constraint("uq_user_roles", "user_roles", ["tenant_id", "user_id", "role_id"], schema=MODULE_SCHEMA)

    # ==================== role_permissions 表 ====================

    # 修改唯一约束：加入 tenant_id
    op.drop_constraint("uq_role_permissions_role_permission", "role_permissions", schema=MODULE_SCHEMA, type_="unique")
    op.create_unique_constraint("uq_role_permissions", "role_permissions", ["tenant_id", "role_id", "permission_id"], schema=MODULE_SCHEMA)


def downgrade() -> None:
    # ==================== role_permissions 表 ====================
    op.drop_constraint("uq_role_permissions", "role_permissions", schema=MODULE_SCHEMA, type_="unique")
    op.create_unique_constraint("uq_role_permissions_role_permission", "role_permissions", ["role_id", "permission_id"], schema=MODULE_SCHEMA)

    # ==================== user_roles 表 ====================
    op.drop_constraint("uq_user_roles", "user_roles", schema=MODULE_SCHEMA, type_="unique")
    op.create_unique_constraint("uq_user_roles_user_role", "user_roles", ["user_id", "role_id"], schema=MODULE_SCHEMA)

    # ==================== menus 表 ====================
    op.drop_index("ix_menus_ref_id", table_name="menus", schema=MODULE_SCHEMA)
    op.drop_index("ix_menus_tenant_id", table_name="menus", schema=MODULE_SCHEMA)
    op.drop_constraint("uq_menus_tenant_code", "menus", schema=MODULE_SCHEMA, type_="unique")
    op.create_unique_constraint("menus_code_key", "menus", ["code"], schema=MODULE_SCHEMA)
    op.drop_column("menus", "ref_id", schema=MODULE_SCHEMA)
    op.drop_column("menus", "tenant_id", schema=MODULE_SCHEMA)

    # ==================== roles 表 ====================
    op.drop_index("ix_roles_ref_id", table_name="roles", schema=MODULE_SCHEMA)
    op.drop_constraint("uq_roles_tenant_code", "roles", schema=MODULE_SCHEMA, type_="unique")
    op.drop_column("roles", "ref_id", schema=MODULE_SCHEMA)

    # ==================== permissions 表 ====================
    op.drop_index("ix_permissions_ref_id", table_name="permissions", schema=MODULE_SCHEMA)
    op.drop_index("ix_permissions_tenant_id", table_name="permissions", schema=MODULE_SCHEMA)
    op.drop_constraint("uq_permissions_tenant_code", "permissions", schema=MODULE_SCHEMA, type_="unique")
    op.create_unique_constraint("permissions_code_key", "permissions", ["code"], schema=MODULE_SCHEMA)
    op.drop_column("permissions", "ref_id", schema=MODULE_SCHEMA)
    op.drop_column("permissions", "tenant_id", schema=MODULE_SCHEMA)
