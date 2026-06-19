"""add tenant_id to iam tables for multi-tenant isolation

Revision ID: 002_iam_tenant_isolation
Revises: 001_iam
Create Date: 2026-06-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_iam_tenant_isolation"
down_revision: Union[str, None] = "001_iam"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 模块 schema
MODULE_SCHEMA = "iam"


def upgrade() -> None:
    """添加 tenant_id 字段以支持多租户隔离"""

    # 1. users 表添加 tenant_id
    op.add_column(
        "users",
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenant.tenants.id", ondelete="CASCADE"), nullable=True, comment="租户ID"),
        schema=MODULE_SCHEMA,
    )

    # 从 user_tenants 推导 tenant_id（使用默认租户）
    op.execute(f"""
        UPDATE {MODULE_SCHEMA}.users u
        SET tenant_id = ut.tenant_id
        FROM {MODULE_SCHEMA}.user_tenants ut
        WHERE u.id = ut.user_id AND ut.is_default = true
    """)

    # 对于没有默认租户的用户，使用第一个租户
    op.execute(f"""
        UPDATE {MODULE_SCHEMA}.users u
        SET tenant_id = ut.tenant_id
        FROM {MODULE_SCHEMA}.user_tenants ut
        WHERE u.id = ut.user_id AND u.tenant_id IS NULL
    """)

    # 设置 NOT NULL 约束
    op.alter_column("users", "tenant_id", nullable=False, schema=MODULE_SCHEMA)
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"], schema=MODULE_SCHEMA)

    # 2. user_roles 表添加 tenant_id
    op.add_column(
        "user_roles",
        sa.Column("tenant_id", sa.String(36), nullable=True, comment="租户ID"),
        schema=MODULE_SCHEMA,
    )

    # 从 users 表推导 tenant_id
    op.execute(f"""
        UPDATE {MODULE_SCHEMA}.user_roles ur
        SET tenant_id = u.tenant_id
        FROM {MODULE_SCHEMA}.users u
        WHERE ur.user_id = u.id
    """)

    # 设置 NOT NULL 约束
    op.alter_column("user_roles", "tenant_id", nullable=False, schema=MODULE_SCHEMA)
    op.create_index("ix_user_roles_tenant_id", "user_roles", ["tenant_id"], schema=MODULE_SCHEMA)

    # 3. role_permissions 表添加 tenant_id
    op.add_column(
        "role_permissions",
        sa.Column("tenant_id", sa.String(36), nullable=True, comment="租户ID"),
        schema=MODULE_SCHEMA,
    )

    # 从 roles 表推导 tenant_id（全局角色的 tenant_id 为 NULL）
    op.execute(f"""
        UPDATE {MODULE_SCHEMA}.role_permissions rp
        SET tenant_id = r.tenant_id
        FROM {MODULE_SCHEMA}.roles r
        WHERE rp.role_id = r.id
    """)

    # 注意：role_permissions 的 tenant_id 可以为 NULL（全局角色）
    # 不设置 NOT NULL 约束
    op.create_index("ix_role_permissions_tenant_id", "role_permissions", ["tenant_id"], schema=MODULE_SCHEMA)

    # 4. user_departments 表添加 tenant_id
    op.add_column(
        "user_departments",
        sa.Column("tenant_id", sa.String(36), nullable=True, comment="租户ID"),
        schema=MODULE_SCHEMA,
    )

    # 从 departments 表推导 tenant_id
    op.execute(f"""
        UPDATE {MODULE_SCHEMA}.user_departments ud
        SET tenant_id = d.tenant_id
        FROM {MODULE_SCHEMA}.departments d
        WHERE ud.department_id = d.id
    """)

    # 设置 NOT NULL 约束
    op.alter_column("user_departments", "tenant_id", nullable=False, schema=MODULE_SCHEMA)
    op.create_index("ix_user_departments_tenant_id", "user_departments", ["tenant_id"], schema=MODULE_SCHEMA)


def downgrade() -> None:
    """移除 tenant_id 字段"""

    # 4. user_departments
    op.drop_index("ix_user_departments_tenant_id", table_name="user_departments", schema=MODULE_SCHEMA)
    op.drop_column("user_departments", "tenant_id", schema=MODULE_SCHEMA)

    # 3. role_permissions
    op.drop_index("ix_role_permissions_tenant_id", table_name="role_permissions", schema=MODULE_SCHEMA)
    op.drop_column("role_permissions", "tenant_id", schema=MODULE_SCHEMA)

    # 2. user_roles
    op.drop_index("ix_user_roles_tenant_id", table_name="user_roles", schema=MODULE_SCHEMA)
    op.drop_column("user_roles", "tenant_id", schema=MODULE_SCHEMA)

    # 1. users
    op.drop_index("ix_users_tenant_id", table_name="users", schema=MODULE_SCHEMA)
    op.drop_column("users", "tenant_id", schema=MODULE_SCHEMA)
