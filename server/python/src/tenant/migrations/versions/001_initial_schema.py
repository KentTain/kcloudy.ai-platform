"""Tenant 模块初始数据库模式

Revision ID: 001_tenant_initial
Revises:
Create Date: 2026-06-28

合并所有迁移的最终状态，创建所有 tenant schema 下的表。
本迁移是破坏性重建，不保留历史数据。

当前包含：
- 资源配置表（database_configs、cache_configs、storage_configs、queue_configs、pubsub_configs）
- 租户管理表（tenants、tenant_admins、tenant_business_configs、tenant_configs、tenant_modules）
- 模块定义表（modules、module_menus、module_permissions、module_roles、module_menu_permissions、module_role_permissions）
- 插件管理表（plugin_definitions、plugin_installations、plugin_marketplaces、plugin_packages）
- 同 schema 内外键

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


def upgrade() -> None:
    # 创建 tenant schema
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # ==================== 资源配置表 ====================

    op.create_table(
        "cache_configs",
        sa.Column("name", sa.String(100), nullable=False, comment="配置名称"),
        sa.Column("host", sa.String(255), nullable=False, comment="缓存主机"),
        sa.Column("port", sa.Integer(), nullable=False, comment="缓存端口"),
        sa.Column("password", sa.Text(), nullable=True, comment="缓存密码（加密）"),
        sa.Column("db", sa.Integer(), nullable=False, comment="数据库编号"),
        sa.Column("prefix", sa.String(50), nullable=True, comment="键前缀"),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False, comment="是否为默认配置"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_cache_configs_name", "cache_configs", ["name"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.cache_configs IS '缓存配置表'")

    op.create_table(
        "database_configs",
        sa.Column("name", sa.String(100), nullable=False, comment="配置名称"),
        sa.Column("type", sa.String(20), nullable=False, comment="数据库类型（postgresql/mysql）"),
        sa.Column("host", sa.String(255), nullable=False, comment="数据库主机"),
        sa.Column("port", sa.Integer(), nullable=False, comment="数据库端口"),
        sa.Column("database", sa.String(100), nullable=False, comment="数据库名称"),
        sa.Column("username", sa.String(100), nullable=False, comment="数据库用户名"),
        sa.Column("password", sa.Text(), nullable=False, comment="数据库密码（加密）"),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False, comment="是否为默认配置"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_database_configs_name", "database_configs", ["name"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.database_configs IS '数据库配置表'")

    op.create_table(
        "storage_configs",
        sa.Column("name", sa.String(100), nullable=False, comment="配置名称"),
        sa.Column("type", sa.String(20), nullable=False, comment="存储类型（minio/s3/oss）"),
        sa.Column("bucket", sa.String(100), nullable=False, comment="存储桶名称"),
        sa.Column("endpoint", sa.String(255), nullable=True, comment="服务端点"),
        sa.Column("access_key", sa.String(100), nullable=True, comment="访问密钥"),
        sa.Column("secret_key", sa.Text(), nullable=True, comment="私密密钥（加密）"),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False, comment="是否为默认配置"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_storage_configs_name", "storage_configs", ["name"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.storage_configs IS '存储配置表'")

    op.create_table(
        "queue_configs",
        sa.Column("name", sa.String(100), nullable=False, comment="配置名称"),
        sa.Column("type", sa.String(20), nullable=False, comment="队列类型（redis/rabbitmq/kafka）"),
        sa.Column("host", sa.String(255), nullable=False, comment="队列主机"),
        sa.Column("port", sa.Integer(), nullable=False, comment="队列端口"),
        sa.Column("username", sa.String(100), nullable=True, comment="用户名"),
        sa.Column("password", sa.Text(), nullable=True, comment="密码（加密）"),
        sa.Column("vhost", sa.String(100), nullable=True, comment="虚拟主机"),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False, comment="是否为默认配置"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_queue_configs_name", "queue_configs", ["name"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.queue_configs IS '队列配置表'")

    op.create_table(
        "pubsub_configs",
        sa.Column("name", sa.String(100), nullable=False, comment="配置名称"),
        sa.Column("type", sa.String(20), nullable=False, comment="发布订阅类型（redis/kafka/nats）"),
        sa.Column("host", sa.String(255), nullable=False, comment="主机地址"),
        sa.Column("port", sa.Integer(), nullable=False, comment="端口"),
        sa.Column("username", sa.String(100), nullable=True, comment="用户名"),
        sa.Column("password", sa.Text(), nullable=True, comment="密码（加密）"),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False, comment="是否为默认配置"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_pubsub_configs_name", "pubsub_configs", ["name"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.pubsub_configs IS '发布订阅配置表'")

    # ==================== 租户管理表 ====================

    op.create_table(
        "tenant_admins",
        sa.Column("username", sa.String(50), nullable=False, comment="用户名"),
        sa.Column("password", sa.String(255), nullable=False, comment="密码哈希"),
        sa.Column("role", sa.String(50), nullable=False, comment="角色编码"),
        sa.Column("is_default", sa.Boolean(), nullable=False, comment="是否默认管理员"),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="是否激活"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenant_admins_username", "tenant_admins", ["username"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.tenant_admins IS '租户管理员表'")

    op.create_table(
        "tenants",
        sa.Column("name", sa.String(100), nullable=False, comment="租户名称"),
        sa.Column("code", sa.String(50), nullable=False, comment="租户编码"),
        sa.Column("status", sa.String(20), nullable=False, comment="状态"),
        sa.Column("contact_name", sa.String(100), nullable=True, comment="联系人姓名"),
        sa.Column("contact_email", sa.String(128), nullable=True, comment="联系人邮箱"),
        sa.Column("contact_phone", sa.String(20), nullable=True, comment="联系人电话"),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True, comment="过期时间"),
        sa.Column("db_config_id", sa.String(36), nullable=True, comment="数据库配置ID"),
        sa.Column("storage_config_id", sa.String(36), nullable=True, comment="存储配置ID"),
        sa.Column("cache_config_id", sa.String(36), nullable=True, comment="缓存配置ID"),
        sa.Column("queue_config_id", sa.String(36), nullable=True, comment="队列配置ID"),
        sa.Column("pubsub_config_id", sa.String(36), nullable=True, comment="发布订阅配置ID"),
        sa.Column("encryption_key", sa.Text(), nullable=True, comment="租户加密密钥(主密钥加密)"),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment="扩展设置"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenants_code", "tenants", ["code"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenants_status", "tenants", ["status"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.tenants IS '租户表'")

    # ==================== 模块定义表 ====================

    op.create_table(
        "modules",
        sa.Column("code", sa.String(50), nullable=False, comment="模块编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="模块名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="模块描述"),
        sa.Column("icon", sa.String(100), nullable=True, comment="图标标识"),
        sa.Column("version", sa.String(20), nullable=False, comment="模块版本"),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="是否启用"),
        sa.Column("is_need", sa.Boolean(), nullable=False, comment="是否必须模块"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        schema=MODULE_SCHEMA,
    )
    op.execute("COMMENT ON TABLE tenant.modules IS '模块定义表'")

    op.create_table(
        "plugin_definitions",
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID，manifest中的author+name，例如alon/tongyi"),
        sa.Column("plugin_unique_identifier", sa.String(256), nullable=False, comment="插件唯一标识符，格式：{plugin_id}:{version}@{校验和}"),
        sa.Column("declaration", postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment="完整声明内容（manifest + 工具/模型声明）。local类型从插件包解析，remote类型从远程获取。包含：configuration、tools_configuration、models_configuration、agent_strategies_configuration"),
        sa.Column("refers", sa.Integer(), nullable=False, comment="引用计数，计算不同租户的引用计数"),
        sa.Column("install_type", sa.String(16), nullable=False, comment="安装类型，local, remote"),
        sa.Column("manifest_type", sa.String(32), nullable=True, comment="清单类型"),
        sa.Column("is_recommended", sa.Boolean(), server_default=sa.text("false"), nullable=False, comment="是否推荐"),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False, comment="是否启用"),
        # 远程插件市场相关字段
        sa.Column("marketplace_id", sa.String(36), nullable=True, comment="来源市场ID，本地注册的为 NULL"),
        sa.Column("remote_plugin_id", sa.String(128), nullable=True, comment="远程市场的插件标识"),
        sa.Column("remote_version", sa.String(32), nullable=True, comment="远程最新版本"),
        sa.Column("local_version", sa.String(32), nullable=True, comment="本地存储版本"),
        sa.Column("update_available", sa.Boolean(), server_default=sa.text("false"), nullable=False, comment="是否有新版本"),
        sa.Column("package_id", sa.String(36), nullable=True, comment="关联的插件包记录"),
        sa.Column("source_type", sa.String(16), server_default="local", nullable=False, comment="来源类型：local, remote"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plugin_unique_identifier"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(op.f("ix_tenant_plugin_definitions_install_type"), "plugin_definitions", ["install_type"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_tenant_plugin_definitions_plugin_id"), "plugin_definitions", ["plugin_id"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.plugin_definitions IS '插件定义表'")

    op.create_table(
        "plugin_installations",
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID"),
        sa.Column("plugin_unique_identifier", sa.String(256), nullable=False, comment="插件唯一标识符"),
        sa.Column("status", sa.String(16), nullable=False, comment="状态: PENDING, ACTIVE, INACTIVE, FAILED"),
        sa.Column("auto_start", sa.Boolean(), nullable=False, comment="是否自动启动"),
        sa.Column("freeze_threshold_hours", sa.Integer(), nullable=False, comment="冻结阈值小时数"),
        sa.Column("plugin_type", sa.String(16), nullable=True, comment="插件类型"),
        sa.Column("runtime_type", sa.String(16), nullable=True, comment="运行时类型"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "plugin_id", name="ix_plugin_installations_tenant_plugin"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(op.f("ix_tenant_plugin_installations_plugin_id"), "plugin_installations", ["plugin_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_tenant_plugin_installations_plugin_unique_identifier"), "plugin_installations", ["plugin_unique_identifier"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_tenant_plugin_installations_tenant_id"), "plugin_installations", ["tenant_id"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.plugin_installations IS '插件安装记录表'")

    # ==================== 插件市场相关表 ====================

    op.create_table(
        "plugin_marketplaces",
        sa.Column("name", sa.String(64), nullable=False, comment="市场名称"),
        sa.Column("code", sa.String(32), nullable=False, comment="市场编码"),
        sa.Column("type", sa.String(32), nullable=False, comment="市场类型：dify, modelscope"),
        sa.Column("url", sa.String(512), nullable=False, comment="市场 API 地址"),
        sa.Column("auth_type", sa.String(16), nullable=False, server_default="none", comment="认证类型：none, api_key, token"),
        sa.Column("auth_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}", comment="认证配置（加密存储）"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="是否启用"),
        sa.Column("sync_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}", comment="同步配置"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True, comment="最后同步时间"),
        sa.Column("last_sync_status", sa.String(16), nullable=True, comment="最后同步状态"),
        sa.Column("description", sa.Text(), nullable=True, comment="市场描述"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenant_plugin_marketplaces_code", "plugin_marketplaces", ["code"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenant_plugin_marketplaces_type", "plugin_marketplaces", ["type"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenant_plugin_marketplaces_enabled", "plugin_marketplaces", ["is_enabled"], schema=MODULE_SCHEMA)

    op.create_table(
        "plugin_packages",
        sa.Column("plugin_id", sa.String(128), nullable=False, comment="插件ID：author/name"),
        sa.Column("version", sa.String(32), nullable=False, comment="版本号"),
        sa.Column("marketplace_id", sa.String(36), nullable=True, comment="来源市场ID"),
        sa.Column("storage_path", sa.String(512), nullable=False, comment="MinIO 存储路径"),
        sa.Column("file_size", sa.BigInteger(), nullable=True, comment="文件大小（字节）"),
        sa.Column("checksum", sa.String(128), nullable=True, comment="SHA256 校验和"),
        sa.Column("manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="解析后的 manifest"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plugin_id", "version", "marketplace_id", name="uq_plugin_packages_plugin_version_marketplace"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenant_plugin_packages_plugin_id", "plugin_packages", ["plugin_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tenant_plugin_packages_marketplace", "plugin_packages", ["marketplace_id"], schema=MODULE_SCHEMA)

    # ==================== 依赖模块的表 ====================

    op.create_table(
        "module_menus",
        sa.Column("module_id", sa.String(36), nullable=False, comment="模块ID"),
        sa.Column("parent_id", sa.String(36), nullable=True, comment="父菜单ID"),
        sa.Column("code", sa.String(100), nullable=False, comment="菜单编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="菜单名称"),
        sa.Column("path", sa.String(200), nullable=False, comment="前端路由路径"),
        sa.Column("icon", sa.String(100), nullable=True, comment="图标标识"),
        sa.Column("is_visible", sa.Boolean(), nullable=False, comment="是否显示"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("tree_leaf", sa.Boolean(), nullable=False, comment="是否为叶子节点"),
        sa.Column("tree_level", sa.Integer(), nullable=False, comment="树层级"),
        sa.Column("tree_sort", sa.Integer(), nullable=False, comment="排序号"),
        sa.Column("tree_sorts", sa.String(512), nullable=False, comment="排序路径"),
        sa.Column("tree_names", sa.String(512), nullable=False, comment="名称路径"),
        sa.Column("parent_ids", sa.String(1024), nullable=False, comment="父ID路径"),
        sa.ForeignKeyConstraint(["module_id"], ["tenant.modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_module_menus_code", "module_menus", ["code"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_tenant_module_menus_parent_id"), "module_menus", ["parent_id"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_tenant_module_menus_tree_level"), "module_menus", ["tree_level"], schema=MODULE_SCHEMA)
    op.create_index(op.f("ix_tenant_module_menus_tree_sort"), "module_menus", ["tree_sort"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.module_menus IS '模块菜单定义表'")

    op.create_table(
        "module_permissions",
        sa.Column("module_id", sa.String(36), nullable=False, comment="模块ID"),
        sa.Column("code", sa.String(100), nullable=False, comment="权限编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="权限名称"),
        sa.Column("resource", sa.String(50), nullable=False, comment="资源名称"),
        sa.Column("action", sa.String(20), nullable=False, comment="操作类型（read/write/delete）"),
        sa.Column("description", sa.Text(), nullable=True, comment="权限描述"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["module_id"], ["tenant.modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_module_permissions_code", "module_permissions", ["code"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.module_permissions IS '模块权限表'")

    op.create_table(
        "module_roles",
        sa.Column("module_id", sa.String(36), nullable=True, comment="模块ID（NULL 表示全局角色）"),
        sa.Column("code", sa.String(50), nullable=False, comment="角色编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="角色名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="角色描述"),
        sa.Column("is_system", sa.Boolean(), nullable=False, comment="是否系统内置角色"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["module_id"], ["tenant.modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_id", "code", name="uq_module_roles_module_code"),
        schema=MODULE_SCHEMA,
    )
    op.create_index(
        "uq_module_roles_global_code",
        "module_roles",
        ["code"],
        unique=True,
        schema=MODULE_SCHEMA,
        postgresql_where=sa.text("module_id IS NULL"),
    )
    op.execute("COMMENT ON TABLE tenant.module_roles IS '模块角色定义表'")

    op.create_table(
        "tenant_business_configs",
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("max_users", sa.Integer(), nullable=False, comment="最大用户数"),
        sa.Column("max_storage_mb", sa.Integer(), nullable=False, comment="最大存储空间（MB）"),
        sa.Column("max_api_calls", sa.Integer(), nullable=False, comment="最大API调用次数"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id"),
        schema=MODULE_SCHEMA,
    )
    op.execute("COMMENT ON TABLE tenant.tenant_business_configs IS '租户业务配置表'")

    op.create_table(
        "tenant_configs",
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("config_key", sa.String(100), nullable=False, comment="配置键"),
        sa.Column("config_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="配置值"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tenant_configs_tenant_id", "tenant_configs", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("uq_tenant_configs_tenant_key", "tenant_configs", ["tenant_id", "config_key"], unique=True, schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.tenant_configs IS '租户配置表'")

    op.create_table(
        "tenant_modules",
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("module_id", sa.String(36), nullable=False, comment="模块ID"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, comment="生效时间"),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True, comment="过期时间"),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="是否启用"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["module_id"], ["tenant.modules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "module_id", name="uq_tenant_modules_tenant_module"),
        schema=MODULE_SCHEMA,
    )
    op.execute("COMMENT ON TABLE tenant.tenant_modules IS '租户模块分配表'")

    # ==================== 关联表 ====================

    op.create_table(
        "module_menu_permissions",
        sa.Column("module_menu_id", sa.String(36), nullable=False, comment="模块菜单ID"),
        sa.Column("module_permission_id", sa.String(36), nullable=False, comment="模块权限ID"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["module_menu_id"], ["tenant.module_menus.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_permission_id"], ["tenant.module_permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_menu_id", "module_permission_id", name="uq_module_menu_permissions_menu_perm"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_module_menu_permissions_menu_id", "module_menu_permissions", ["module_menu_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_module_menu_permissions_permission_id", "module_menu_permissions", ["module_permission_id"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.module_menu_permissions IS '模块菜单-权限关联表'")

    op.create_table(
        "module_role_permissions",
        sa.Column("module_role_id", sa.String(36), nullable=False, comment="模块角色ID"),
        sa.Column("module_permission_id", sa.String(36), nullable=False, comment="模块权限ID"),
        sa.Column("id", sa.String(36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["module_permission_id"], ["tenant.module_permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_role_id"], ["tenant.module_roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_role_id", "module_permission_id", name="uq_module_role_permissions_role_perm"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_module_role_permissions_role_id", "module_role_permissions", ["module_role_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_module_role_permissions_permission_id", "module_role_permissions", ["module_permission_id"], schema=MODULE_SCHEMA)
    op.execute("COMMENT ON TABLE tenant.module_role_permissions IS '模块角色-权限关联表'")


def downgrade() -> None:
    # 删除所有表和 schema（CASCADE 自动处理依赖顺序）
    op.execute(f"DROP SCHEMA IF EXISTS {MODULE_SCHEMA} CASCADE")
