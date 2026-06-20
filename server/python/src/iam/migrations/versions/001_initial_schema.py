"""IAM 模块初始数据库模式

Revision ID: 001_iam_initial
Revises:
Create Date: 2026-06-20

合并原 001~007 迁移的最终状态，创建所有 iam schema 下的表。
本迁移是破坏性重建，不保留历史数据。

关键合并点：
- users 表包含 tenant_id（NOT NULL，FK -> tenant.tenants）
- roles 表包含 tenant_id（FK -> tenant.tenants）和 ref_id
- permissions 表包含 tenant_id 和 ref_id，唯一约束为 (tenant_id, code)
- menus 表包含 tenant_id 和 ref_id，唯一约束为 (tenant_id, code)
- organizations 和 menus 表的 parent_id 无外键约束（TreeNodeMixin 虚拟根节点设计）
- user_roles 和 role_permissions 唯一约束包含 tenant_id

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_iam_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "iam"


def upgrade() -> None:
    # 创建 iam schema
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # ==================== 用户与认证表 ====================

    # 创建 users 表（最终状态：含 tenant_id NOT NULL）
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenant.tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("username", sa.String(50), unique=True, nullable=False, comment="用户名"),
        sa.Column("email", sa.String(128), unique=True, nullable=True, comment="邮箱"),
        sa.Column("phone", sa.String(20), unique=True, nullable=True, comment="手机号"),
        sa.Column("password_hash", sa.String(255), nullable=True, comment="密码哈希"),
        sa.Column("nickname", sa.String(100), nullable=True, comment="昵称"),
        sa.Column("avatar", sa.String(500), nullable=True, comment="头像URL"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="状态"),
        sa.Column("profile_completed", sa.Boolean, nullable=False, server_default="true", comment="信息是否完整"),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default="false", comment="邮箱是否已验证"),
        sa.Column("is_phone_verified", sa.Boolean, nullable=False, server_default="false", comment="手机是否已验证"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True, comment="最后登录时间"),
        sa.Column("last_login_ip", sa.String(45), nullable=True, comment="最后登录IP"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_users_username", "users", ["username"], schema=MODULE_SCHEMA)
    op.create_index("ix_users_email", "users", ["email"], schema=MODULE_SCHEMA)
    op.create_index("ix_users_phone", "users", ["phone"], schema=MODULE_SCHEMA)
    op.create_index("ix_users_status", "users", ["status"], schema=MODULE_SCHEMA)

    # 创建 roles 表（最终状态：含 tenant_id、ref_id，唯一约束为 tenant_id+code）
    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenant.tenants.id", ondelete="CASCADE"), nullable=True, comment="租户ID"),
        sa.Column("code", sa.String(50), nullable=False, comment="角色编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="角色名称"),
        sa.Column("description", sa.Text, nullable=True, comment="角色描述"),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="false", comment="是否系统内置角色"),
        sa.Column("ref_id", sa.String(36), nullable=True, comment="模块定义层关联ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_roles_code", "roles", ["code"], schema=MODULE_SCHEMA)
    op.create_index("ix_roles_ref_id", "roles", ["ref_id"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_roles_tenant_code", "roles", ["tenant_id", "code"], schema=MODULE_SCHEMA)

    # 创建 permissions 表（最终状态：含 tenant_id、ref_id，唯一约束为 tenant_id+code）
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=True, comment="租户ID（NULL 表示全局权限）"),
        sa.Column("code", sa.String(100), nullable=False, comment="权限编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="权限名称"),
        sa.Column("resource", sa.String(50), nullable=False, comment="资源名称"),
        sa.Column("action", sa.String(20), nullable=False, comment="操作类型"),
        sa.Column("description", sa.Text, nullable=True, comment="权限描述"),
        sa.Column("ref_id", sa.String(36), nullable=True, comment="模块定义层关联ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_permissions_tenant_id", "permissions", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_permissions_code", "permissions", ["code"], schema=MODULE_SCHEMA)
    op.create_index("ix_permissions_resource", "permissions", ["resource"], schema=MODULE_SCHEMA)
    op.create_index("ix_permissions_ref_id", "permissions", ["ref_id"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_permissions_tenant_code", "permissions", ["tenant_id", "code"], schema=MODULE_SCHEMA)

    # 创建 organizations 表（最终状态：parent_id 无外键约束）
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("parent_id", sa.String(36), nullable=True, comment="父组织ID"),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenant.tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("name", sa.String(100), nullable=False, comment="组织名称"),
        sa.Column("code", sa.String(50), nullable=True, comment="组织编码"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0", comment="排序号"),
        sa.Column("leader_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.users.id", ondelete="SET NULL"), nullable=True, comment="组织负责人ID"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="状态"),
        # TreeNodeMixin 字段
        sa.Column("tree_leaf", sa.Boolean, nullable=False, server_default="true", comment="是否叶子节点"),
        sa.Column("tree_level", sa.Integer, nullable=False, server_default="0", comment="树层级"),
        sa.Column("tree_sort", sa.Integer, nullable=False, server_default="0", comment="排序号"),
        sa.Column("tree_sorts", sa.String(500), nullable=False, server_default="", comment="排序路径"),
        sa.Column("tree_names", sa.String(500), nullable=False, server_default="", comment="名称路径"),
        sa.Column("parent_ids", sa.String(500), nullable=False, server_default="DEFAULT_TREE_ROOT_ID,", comment="父ID路径"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_organizations_tenant_id", "organizations", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_organizations_parent_id", "organizations", ["parent_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_organizations_leader_id", "organizations", ["leader_id"], schema=MODULE_SCHEMA)

    # ==================== 关联表 ====================

    # 创建 user_roles 表（最终状态：含 tenant_id NOT NULL，唯一约束含 tenant_id）
    op.create_table(
        "user_roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("user_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("role_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_user_roles_tenant_id", "user_roles", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_user_roles", "user_roles", ["tenant_id", "user_id", "role_id"], schema=MODULE_SCHEMA)

    # 创建 role_permissions 表（最终状态：含 tenant_id，唯一约束含 tenant_id）
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=True, comment="租户ID"),
        sa.Column("role_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID"),
        sa.Column("permission_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.permissions.id", ondelete="CASCADE"), nullable=False, comment="权限ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_role_permissions_tenant_id", "role_permissions", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_role_permissions", "role_permissions", ["tenant_id", "role_id", "permission_id"], schema=MODULE_SCHEMA)

    # 创建 user_organizations 表（最终状态：含 tenant_id NOT NULL）
    op.create_table(
        "user_organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("user_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.organizations.id", ondelete="CASCADE"), nullable=False, comment="组织ID"),
        sa.Column("is_leader", sa.Boolean, nullable=False, server_default="false", comment="是否组织负责人"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_user_organizations_tenant_id", "user_organizations", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_user_organizations_user_id", "user_organizations", ["user_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_user_organizations_organization_id", "user_organizations", ["organization_id"], schema=MODULE_SCHEMA)

    # 创建 user_tenants 表
    op.create_table(
        "user_tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, comment="用户ID"),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenant.tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false", comment="是否默认租户"),
        sa.Column("role", sa.String(20), nullable=False, server_default="member", comment="角色"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_user_tenants_user_id", "user_tenants", ["user_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_user_tenants_tenant_id", "user_tenants", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_user_tenants_user_tenant", "user_tenants", ["user_id", "tenant_id"], schema=MODULE_SCHEMA)

    # 创建 oauth_connections 表
    op.create_table(
        "oauth_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"),
        sa.Column("provider", sa.String(20), nullable=False, comment="OAuth提供商"),
        sa.Column("provider_user_id", sa.String(100), nullable=False, comment="第三方用户ID"),
        sa.Column("access_token", sa.Text, nullable=True, comment="访问令牌"),
        sa.Column("refresh_token", sa.Text, nullable=True, comment="刷新令牌"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True, comment="令牌过期时间"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_oauth_connections_user_id", "oauth_connections", ["user_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_oauth_connections_provider", "oauth_connections", ["provider"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_oauth_provider_user", "oauth_connections", ["provider", "provider_user_id"], schema=MODULE_SCHEMA)

    # ==================== 系统设置表 ====================

    # 创建 system_settings 表
    op.create_table(
        "system_settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenant.tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("code", sa.String(20), nullable=False, comment="设置编号"),
        sa.Column("name", sa.String(256), nullable=False, comment="名称"),
        sa.Column("display_name", sa.String(512), nullable=True, comment="显示名称"),
        sa.Column("description", sa.String(4000), nullable=True, comment="描述"),
        sa.Column("can_edit", sa.Boolean, nullable=False, server_default="true", comment="是否能编辑"),
        sa.Column("is_require", sa.Boolean, nullable=False, server_default="false", comment="是否必须"),
        sa.Column("index", sa.Integer, nullable=False, server_default="0", comment="排序"),
        sa.Column("application_id", sa.String(36), nullable=True, comment="应用程序Id"),
        sa.Column("application_name", sa.String(128), nullable=True, comment="应用程序名称"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_unique_constraint("uq_system_settings_tenant_code", "system_settings", ["tenant_id", "code"], schema=MODULE_SCHEMA)
    op.create_index("ix_system_settings_tenant_id", "system_settings", ["tenant_id"], schema=MODULE_SCHEMA)

    # 创建 system_setting_attributes 表
    op.create_table(
        "system_setting_attributes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenant.tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("setting_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.system_settings.id", ondelete="CASCADE"), nullable=False, comment="配置Id"),
        sa.Column("data_type", sa.String(20), nullable=False, server_default="string", comment="属性数据类型"),
        sa.Column("name", sa.String(256), nullable=False, comment="属性值名称"),
        sa.Column("display_name", sa.String(512), nullable=True, comment="显示名称"),
        sa.Column("description", sa.String(4000), nullable=True, comment="描述"),
        sa.Column("value", sa.Text, nullable=True, comment="属性值"),
        sa.Column("ext_data", postgresql.JSONB, nullable=True, comment="扩展数据"),
        sa.Column("can_edit", sa.Boolean, nullable=False, server_default="true", comment="是否能编辑"),
        sa.Column("is_require", sa.Boolean, nullable=False, server_default="false", comment="是否必须"),
        sa.Column("index", sa.Integer, nullable=False, server_default="0", comment="排序"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_unique_constraint("uq_system_setting_attributes_setting_name", "system_setting_attributes", ["setting_id", "name"], schema=MODULE_SCHEMA)
    op.create_index("ix_system_setting_attributes_setting_id", "system_setting_attributes", ["setting_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_system_setting_attributes_tenant_id", "system_setting_attributes", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 菜单表 ====================

    # 创建 menus 表（最终状态：含 tenant_id、ref_id，parent_id 无外键约束，唯一约束为 tenant_id+code）
    op.create_table(
        "menus",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("parent_id", sa.String(36), nullable=True, comment="父菜单ID"),
        sa.Column("module", sa.String(50), nullable=False, comment="所属模块标识"),
        sa.Column("tenant_id", sa.String(36), nullable=True, comment="租户ID（NULL 表示全局菜单）"),
        sa.Column("code", sa.String(100), nullable=False, comment="菜单编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="菜单名称"),
        sa.Column("path", sa.String(200), nullable=False, comment="前端路由路径"),
        sa.Column("icon", sa.String(100), nullable=True, comment="图标标识"),
        sa.Column("is_visible", sa.Boolean, nullable=False, server_default="true", comment="是否显示"),
        sa.Column("deployment_base_url", sa.String(500), nullable=True, comment="模块部署地址"),
        sa.Column("ref_id", sa.String(36), nullable=True, comment="模块定义层关联ID"),
        # TreeNodeMixin 字段
        sa.Column("tree_leaf", sa.Boolean, nullable=False, server_default="true", comment="是否叶子节点"),
        sa.Column("tree_level", sa.Integer, nullable=False, server_default="0", comment="树层级"),
        sa.Column("tree_sort", sa.Integer, nullable=False, server_default="0", comment="排序号"),
        sa.Column("tree_sorts", sa.String(500), nullable=False, server_default="", comment="排序路径"),
        sa.Column("tree_names", sa.String(500), nullable=False, server_default="", comment="名称路径"),
        sa.Column("parent_ids", sa.String(500), nullable=False, server_default="DEFAULT_TREE_ROOT_ID,", comment="父ID路径"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_menus_parent_id", "menus", ["parent_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_menus_module", "menus", ["module"], schema=MODULE_SCHEMA)
    op.create_index("ix_menus_tenant_id", "menus", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_menus_code", "menus", ["code"], schema=MODULE_SCHEMA)
    op.create_index("ix_menus_ref_id", "menus", ["ref_id"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_menus_tenant_code", "menus", ["tenant_id", "code"], schema=MODULE_SCHEMA)

    # 创建 menu_permissions 表
    op.create_table(
        "menu_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("menu_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.menus.id", ondelete="CASCADE"), nullable=False, comment="菜单ID"),
        sa.Column("permission_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.permissions.id", ondelete="CASCADE"), nullable=False, comment="权限ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_menu_permissions_menu_id", "menu_permissions", ["menu_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_menu_permissions_permission_id", "menu_permissions", ["permission_id"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_menu_permissions_menu_permission", "menu_permissions", ["menu_id", "permission_id"], schema=MODULE_SCHEMA)


def downgrade() -> None:
    # 删除所有表和 schema（CASCADE 自动处理依赖顺序）
    op.execute(f"DROP SCHEMA IF EXISTS {MODULE_SCHEMA} CASCADE")
