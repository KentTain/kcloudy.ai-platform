"""add tenant module system tables and resource config columns

Revision ID: 002_tenant_module_system
Revises: 001_tenant
Create Date: 2026-06-09

创建租户模块系统相关的 11 张新表，并向 tenants 表新增 5 列资源配置关联字段。

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_tenant_module_system"
down_revision: Union[str, None] = "001_tenant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_database_configs_name", "database_configs", ["name"], schema=MODULE_SCHEMA)

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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_storage_configs_name", "storage_configs", ["name"], schema=MODULE_SCHEMA)

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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_cache_configs_name", "cache_configs", ["name"], schema=MODULE_SCHEMA)

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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_queue_configs_name", "queue_configs", ["name"], schema=MODULE_SCHEMA)

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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_pubsub_configs_name", "pubsub_configs", ["name"], schema=MODULE_SCHEMA)

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

    # ==================== tenants 表新增列 ====================

    op.add_column("tenants", sa.Column("db_config_id", sa.String(36), nullable=True, comment="数据库配置ID"), schema=MODULE_SCHEMA)
    op.add_column("tenants", sa.Column("storage_config_id", sa.String(36), nullable=True, comment="存储配置ID"), schema=MODULE_SCHEMA)
    op.add_column("tenants", sa.Column("cache_config_id", sa.String(36), nullable=True, comment="缓存配置ID"), schema=MODULE_SCHEMA)
    op.add_column("tenants", sa.Column("queue_config_id", sa.String(36), nullable=True, comment="队列配置ID"), schema=MODULE_SCHEMA)
    op.add_column("tenants", sa.Column("pubsub_config_id", sa.String(36), nullable=True, comment="发布订阅配置ID"), schema=MODULE_SCHEMA)

    op.create_index("ix_tenants_db_config_id", "tenants", ["db_config_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_storage_config_id", "tenants", ["storage_config_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_cache_config_id", "tenants", ["cache_config_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_queue_config_id", "tenants", ["queue_config_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_pubsub_config_id", "tenants", ["pubsub_config_id"], schema=MODULE_SCHEMA)


def downgrade() -> None:
    # tenants 表移除新增列
    op.drop_index("ix_tenants_pubsub_config_id", table_name="tenants", schema=MODULE_SCHEMA)
    op.drop_index("ix_tenants_queue_config_id", table_name="tenants", schema=MODULE_SCHEMA)
    op.drop_index("ix_tenants_cache_config_id", table_name="tenants", schema=MODULE_SCHEMA)
    op.drop_index("ix_tenants_storage_config_id", table_name="tenants", schema=MODULE_SCHEMA)
    op.drop_index("ix_tenants_db_config_id", table_name="tenants", schema=MODULE_SCHEMA)

    op.drop_column("tenants", "pubsub_config_id", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "queue_config_id", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "cache_config_id", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "storage_config_id", schema=MODULE_SCHEMA)
    op.drop_column("tenants", "db_config_id", schema=MODULE_SCHEMA)

    # 删除模块系统表（按依赖顺序逆序）
    op.drop_table("tenant_modules", schema=MODULE_SCHEMA)
    op.drop_index("ix_module_role_permissions_permission_id", table_name="module_role_permissions", schema=MODULE_SCHEMA)
    op.drop_index("ix_module_role_permissions_role_id", table_name="module_role_permissions", schema=MODULE_SCHEMA)
    op.drop_table("module_role_permissions", schema=MODULE_SCHEMA)
    op.drop_table("module_roles", schema=MODULE_SCHEMA)
    op.drop_index("ix_module_permissions_code", table_name="module_permissions", schema=MODULE_SCHEMA)
    op.drop_table("module_permissions", schema=MODULE_SCHEMA)
    op.drop_index("ix_module_menus_code", table_name="module_menus", schema=MODULE_SCHEMA)
    op.drop_table("module_menus", schema=MODULE_SCHEMA)
    op.drop_table("modules", schema=MODULE_SCHEMA)
    op.drop_table("tenant_business_configs", schema=MODULE_SCHEMA)

    # 删除资源配置表
    op.drop_index("ix_pubsub_configs_name", table_name="pubsub_configs", schema=MODULE_SCHEMA)
    op.drop_table("pubsub_configs", schema=MODULE_SCHEMA)
    op.drop_index("ix_queue_configs_name", table_name="queue_configs", schema=MODULE_SCHEMA)
    op.drop_table("queue_configs", schema=MODULE_SCHEMA)
    op.drop_index("ix_cache_configs_name", table_name="cache_configs", schema=MODULE_SCHEMA)
    op.drop_table("cache_configs", schema=MODULE_SCHEMA)
    op.drop_index("ix_storage_configs_name", table_name="storage_configs", schema=MODULE_SCHEMA)
    op.drop_table("storage_configs", schema=MODULE_SCHEMA)
    op.drop_index("ix_database_configs_name", table_name="database_configs", schema=MODULE_SCHEMA)
    op.drop_table("database_configs", schema=MODULE_SCHEMA)
