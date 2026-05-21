"""add iam tables

Revision ID: 002_iam
Revises: 001_tenant
Create Date: 2026-05-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_iam"
down_revision: Union[str, None] = "001_tenant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 users 表
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, comment="用户名"),
        sa.Column("email", sa.String(128), unique=True, nullable=True, comment="邮箱"),
        sa.Column("phone", sa.String(20), unique=True, nullable=True, comment="手机号"),
        sa.Column("password_hash", sa.String(255), nullable=True, comment="密码哈希"),
        sa.Column("nickname", sa.String(100), nullable=True, comment="昵称"),
        sa.Column("avatar", sa.String(500), nullable=True, comment="头像 URL"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="状态"),
        sa.Column("profile_completed", sa.Boolean, nullable=False, server_default="true", comment="信息是否完整"),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default="false", comment="邮箱是否已验证"),
        sa.Column("is_phone_verified", sa.Boolean, nullable=False, server_default="false", comment="手机是否已验证"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True, comment="最后登录时间"),
        sa.Column("last_login_ip", sa.String(45), nullable=True, comment="最后登录 IP"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_phone", "users", ["phone"])
    op.create_index("ix_users_status", "users", ["status"])

    # 创建 oauth_connections 表
    op.create_table(
        "oauth_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("provider", sa.String(20), nullable=False, comment="OAuth 提供商"),
        sa.Column("provider_user_id", sa.String(100), nullable=False, comment="第三方用户ID"),
        sa.Column("access_token", sa.Text, nullable=True, comment="访问令牌"),
        sa.Column("refresh_token", sa.Text, nullable=True, comment="刷新令牌"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True, comment="令牌过期时间"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_oauth_connections_user_id", "oauth_connections", ["user_id"])
    op.create_index("ix_oauth_connections_provider", "oauth_connections", ["provider"])
    op.create_unique_constraint("uq_oauth_provider_user", "oauth_connections", ["provider", "provider_user_id"])

    # 创建 departments 表
    op.create_table(
        "departments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, comment="父部门ID"),
        sa.Column("name", sa.String(100), nullable=False, comment="部门名称"),
        sa.Column("code", sa.String(50), nullable=True, comment="部门编码"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0", comment="排序号"),
        sa.Column("leader_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="部门负责人ID"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="状态"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_departments_tenant_id", "departments", ["tenant_id"])
    op.create_index("ix_departments_parent_id", "departments", ["parent_id"])
    op.create_index("ix_departments_leader_id", "departments", ["leader_id"])

    # 创建 user_departments 表
    op.create_table(
        "user_departments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("department_id", sa.String(36), sa.ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, comment="部门ID"),
        sa.Column("is_leader", sa.Boolean, nullable=False, server_default="false", comment="是否部门负责人"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_user_departments_user_id", "user_departments", ["user_id"])
    op.create_index("ix_user_departments_department_id", "user_departments", ["department_id"])

    # 创建 roles 表
    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, comment="租户ID"),
        sa.Column("code", sa.String(50), nullable=False, comment="角色编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="角色名称"),
        sa.Column("description", sa.Text, nullable=True, comment="角色描述"),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="false", comment="是否系统内置角色"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])
    op.create_index("ix_roles_code", "roles", ["code"])

    # 创建 permissions 表
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(100), unique=True, nullable=False, comment="权限编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="权限名称"),
        sa.Column("resource", sa.String(50), nullable=False, comment="资源名称"),
        sa.Column("action", sa.String(20), nullable=False, comment="操作类型"),
        sa.Column("description", sa.Text, nullable=True, comment="权限描述"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"])
    op.create_index("ix_permissions_resource", "permissions", ["resource"])

    # 创建 user_roles 表
    op.create_table(
        "user_roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_unique_constraint("uq_user_roles_user_role", "user_roles", ["user_id", "role_id"])

    # 创建 role_permissions 表
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID"),
        sa.Column("permission_id", sa.String(36), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, comment="权限ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])
    op.create_unique_constraint("uq_role_permissions_role_permission", "role_permissions", ["role_id", "permission_id"])


def downgrade() -> None:
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("user_departments")
    op.drop_table("departments")
    op.drop_table("oauth_connections")
    op.drop_table("users")
