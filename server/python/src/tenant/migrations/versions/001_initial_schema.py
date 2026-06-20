"""租户模块初始数据库模式

Revision ID: 001_tenant_initial
Revises:
Create Date: 2026-06-20

合并原 001~008 迁移的最终状态，创建所有 tenant schema 下的表。
本迁移是破坏性重建，不保留历史数据。

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_tenant_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"

# 资源配置表名列表
RESOURCE_CONFIG_TABLES = [
    "database_configs",
    "cache_configs",
    "storage_configs",
    "queue_configs",
    "pubsub_configs",
]


def upgrade() -> None:
    # 创建 tenant schema
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # ==================== 租户核心表 ====================

    # 创建 tenants 表（最终状态：含资源配置关联字段，无内嵌配置字段）
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, comment="租户名称"),
        sa.Column("code", sa.String(50), unique=True, nullable=False, comment="租户编码"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="状态"),
        sa.Column("contact_name", sa.String(100), nullable=True, comment="联系人姓名"),
        sa.Column("contact_email", sa.String(128), nullable=True, comment="联系人邮箱"),
        sa.Column("contact_phone", sa.String(20), nullable=True, comment="联系人电话"),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True, comment="过期时间"),
        # 加密密钥
        sa.Column("encryption_key", sa.Text, nullable=True, comment="租户加密密钥(主密钥加密)"),
        # 资源配置关联字段
        sa.Column("db_config_id", sa.String(36), nullable=True, comment="数据库配置ID"),
        sa.Column("storage_config_id", sa.String(36), nullable=True, comment="存储配置ID"),
        sa.Column("cache_config_id", sa.String(36), nullable=True, comment="缓存配置ID"),
        sa.Column("queue_config_id", sa.String(36), nullable=True, comment="队列配置ID"),
        sa.Column("pubsub_config_id", sa.String(36), nullable=True, comment="发布订阅配置ID"),
        # 扩展设置
        sa.Column("settings", postgresql.JSONB, nullable=False, server_default="{}", comment="扩展设置"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenants_code", "tenants", ["code"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_status", "tenants", ["status"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_db_config_id", "tenants", ["db_config_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_storage_config_id", "tenants", ["storage_config_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_cache_config_id", "tenants", ["cache_config_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_queue_config_id", "tenants", ["queue_config_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_pubsub_config_id", "tenants", ["pubsub_config_id"], schema=MODULE_SCHEMA)

    # 创建 tenant_configs 表
    op.create_table(
        "tenant_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("config_key", sa.String(100), nullable=False, comment="配置键"),
        sa.Column("config_value", postgresql.JSONB, nullable=True, comment="配置值"),
        sa.Column("description", sa.Text, nullable=True, comment="描述"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenant_configs_tenant_id", "tenant_configs", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("uq_tenant_configs_tenant_key", "tenant_configs", ["tenant_id", "config_key"], unique=True, schema=MODULE_SCHEMA)

    # 创建 tenant_admins 表
    op.create_table(
        "tenant_admins",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, comment="用户名"),
        sa.Column("password", sa.String(255), nullable=False, comment="密码哈希"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false", comment="是否默认管理员"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true", comment="是否激活"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenant_admins_username", "tenant_admins", ["username"], schema=MODULE_SCHEMA)

    # ==================== 资源配置表 ====================

    # 创建 database_configs 表
    op.create_table(
        "database_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, comment="配置名称"),
        sa.Column("type", sa.String(20), nullable=False, comment="数据库类型（postgresql/mysql）"),
        sa.Column("host", sa.String(255), nullable=False, comment="数据库主机"),
        sa.Column("port", sa.Integer, nullable=False, comment="数据库端口"),
        sa.Column("database", sa.String(100), nullable=False, comment="数据库名称"),
        sa.Column("username", sa.String(100), nullable=False, comment="数据库用户名"),
        sa.Column("password", sa.Text, nullable=False, comment="数据库密码（加密）"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false", comment="是否为默认配置"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_database_configs_name", "database_configs", ["name"], schema=MODULE_SCHEMA)
    op.create_index(
        "uix_database_configs_default",
        "database_configs",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
        schema=MODULE_SCHEMA,
    )

    # 创建 storage_configs 表
    op.create_table(
        "storage_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, comment="配置名称"),
        sa.Column("type", sa.String(20), nullable=False, comment="存储类型（minio/s3/oss）"),
        sa.Column("bucket", sa.String(100), nullable=False, comment="存储桶名称"),
        sa.Column("endpoint", sa.String(255), nullable=True, comment="服务端点"),
        sa.Column("access_key", sa.String(100), nullable=True, comment="访问密钥"),
        sa.Column("secret_key", sa.Text, nullable=True, comment="私密密钥（加密）"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false", comment="是否为默认配置"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_storage_configs_name", "storage_configs", ["name"], schema=MODULE_SCHEMA)
    op.create_index(
        "uix_storage_configs_default",
        "storage_configs",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
        schema=MODULE_SCHEMA,
    )

    # 创建 cache_configs 表
    op.create_table(
        "cache_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, comment="配置名称"),
        sa.Column("host", sa.String(255), nullable=False, comment="缓存主机"),
        sa.Column("port", sa.Integer, nullable=False, comment="缓存端口"),
        sa.Column("password", sa.Text, nullable=True, comment="缓存密码（加密）"),
        sa.Column("db", sa.Integer, nullable=False, server_default="0", comment="数据库编号"),
        sa.Column("prefix", sa.String(50), nullable=True, comment="键前缀"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false", comment="是否为默认配置"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_cache_configs_name", "cache_configs", ["name"], schema=MODULE_SCHEMA)
    op.create_index(
        "uix_cache_configs_default",
        "cache_configs",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
        schema=MODULE_SCHEMA,
    )

    # 创建 queue_configs 表
    op.create_table(
        "queue_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, comment="配置名称"),
        sa.Column("type", sa.String(20), nullable=False, comment="队列类型（redis/rabbitmq/kafka）"),
        sa.Column("host", sa.String(255), nullable=False, comment="队列主机"),
        sa.Column("port", sa.Integer, nullable=False, comment="队列端口"),
        sa.Column("username", sa.String(100), nullable=True, comment="用户名"),
        sa.Column("password", sa.Text, nullable=True, comment="密码（加密）"),
        sa.Column("vhost", sa.String(100), nullable=True, comment="虚拟主机"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false", comment="是否为默认配置"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_queue_configs_name", "queue_configs", ["name"], schema=MODULE_SCHEMA)
    op.create_index(
        "uix_queue_configs_default",
        "queue_configs",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
        schema=MODULE_SCHEMA,
    )

    # 创建 pubsub_configs 表
    op.create_table(
        "pubsub_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, comment="配置名称"),
        sa.Column("type", sa.String(20), nullable=False, comment="发布订阅类型（redis/kafka/nats）"),
        sa.Column("host", sa.String(255), nullable=False, comment="主机地址"),
        sa.Column("port", sa.Integer, nullable=False, comment="端口"),
        sa.Column("username", sa.String(100), nullable=True, comment="用户名"),
        sa.Column("password", sa.Text, nullable=True, comment="密码（加密）"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false", comment="是否为默认配置"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_pubsub_configs_name", "pubsub_configs", ["name"], schema=MODULE_SCHEMA)
    op.create_index(
        "uix_pubsub_configs_default",
        "pubsub_configs",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
        schema=MODULE_SCHEMA,
    )

    # ==================== 租户业务配置表 ====================

    # 创建 tenant_business_configs 表
    op.create_table(
        "tenant_business_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.tenants.id", ondelete="CASCADE"), nullable=False, unique=True, comment="租户ID"),
        sa.Column("max_users", sa.Integer, nullable=False, server_default="100", comment="最大用户数"),
        sa.Column("max_storage_mb", sa.Integer, nullable=False, server_default="1024", comment="最大存储空间（MB）"),
        sa.Column("max_api_calls", sa.Integer, nullable=False, server_default="10000", comment="最大API调用次数"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenant_business_configs_tenant_id", "tenant_business_configs", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 模块定义层表 ====================

    # 创建 modules 表
    op.create_table(
        "modules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False, comment="模块编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="模块名称"),
        sa.Column("description", sa.Text, nullable=True, comment="模块描述"),
        sa.Column("icon", sa.String(100), nullable=True, comment="图标标识"),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0", comment="模块版本"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true", comment="是否启用"),
        sa.Column("is_need", sa.Boolean, nullable=False, server_default="false", comment="是否必须模块"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_modules_code", "modules", ["code"], schema=MODULE_SCHEMA)

    # 创建 module_menus 表
    op.create_table(
        "module_menus",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("module_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.modules.id", ondelete="CASCADE"), nullable=False, comment="模块ID"),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.module_menus.id", ondelete="SET NULL"), nullable=True, comment="父菜单ID"),
        sa.Column("code", sa.String(100), unique=True, nullable=False, comment="菜单编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="菜单名称"),
        sa.Column("path", sa.String(200), nullable=False, comment="前端路由路径"),
        sa.Column("icon", sa.String(100), nullable=True, comment="图标标识"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0", comment="排序号"),
        sa.Column("is_visible", sa.Boolean, nullable=False, server_default="true", comment="是否显示"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_module_menus_module_id", "module_menus", ["module_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_module_menus_parent_id", "module_menus", ["parent_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_module_menus_code", "module_menus", ["code"], schema=MODULE_SCHEMA)

    # 创建 module_permissions 表
    op.create_table(
        "module_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("module_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.modules.id", ondelete="CASCADE"), nullable=False, comment="模块ID"),
        sa.Column("code", sa.String(100), unique=True, nullable=False, comment="权限编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="权限名称"),
        sa.Column("resource", sa.String(50), nullable=False, comment="资源名称"),
        sa.Column("action", sa.String(20), nullable=False, comment="操作类型（read/write/delete）"),
        sa.Column("description", sa.Text, nullable=True, comment="权限描述"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_module_permissions_module_id", "module_permissions", ["module_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_module_permissions_code", "module_permissions", ["code"], schema=MODULE_SCHEMA)

    # 创建 module_roles 表
    op.create_table(
        "module_roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("module_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.modules.id", ondelete="CASCADE"), nullable=False, comment="模块ID"),
        sa.Column("code", sa.String(50), nullable=False, comment="角色编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="角色名称"),
        sa.Column("description", sa.Text, nullable=True, comment="角色描述"),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="false", comment="是否系统内置角色"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_module_roles_module_id", "module_roles", ["module_id"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_module_roles_module_code", "module_roles", ["module_id", "code"], schema=MODULE_SCHEMA)

    # 创建 module_role_permissions 表
    op.create_table(
        "module_role_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("module_role_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.module_roles.id", ondelete="CASCADE"), nullable=False, comment="模块角色ID"),
        sa.Column("module_permission_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.module_permissions.id", ondelete="CASCADE"), nullable=False, comment="模块权限ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_unique_constraint(
        "uq_module_role_permissions_role_perm", "module_role_permissions",
        ["module_role_id", "module_permission_id"], schema=MODULE_SCHEMA,
    )
    op.create_index("ix_module_role_permissions_role_id", "module_role_permissions", ["module_role_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_module_role_permissions_permission_id", "module_role_permissions", ["module_permission_id"], schema=MODULE_SCHEMA)

    # 创建 tenant_modules 表
    op.create_table(
        "tenant_modules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.tenants.id", ondelete="CASCADE"), nullable=False, comment="租户ID"),
        sa.Column("module_id", sa.String(36), sa.ForeignKey(f"{MODULE_SCHEMA}.modules.id", ondelete="CASCADE"), nullable=False, comment="模块ID"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, comment="生效时间"),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True, comment="过期时间"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true", comment="是否启用"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenant_modules_tenant_id", "tenant_modules", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenant_modules_module_id", "tenant_modules", ["module_id"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_tenant_modules_tenant_module", "tenant_modules", ["tenant_id", "module_id"], schema=MODULE_SCHEMA)

    # 创建 module_menu_permissions 表
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
    op.create_unique_constraint(
        "uq_module_menu_permissions_menu_perm",
        "module_menu_permissions",
        ["module_menu_id", "module_permission_id"],
        schema=MODULE_SCHEMA,
    )
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
    # 删除所有表和 schema（CASCADE 自动处理依赖顺序）
    op.execute(f"DROP SCHEMA IF EXISTS {MODULE_SCHEMA} CASCADE")
