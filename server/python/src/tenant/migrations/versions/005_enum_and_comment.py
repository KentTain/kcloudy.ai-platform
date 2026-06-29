"""补充表级comment并将字段从String改为EnumType

Revision ID: 005_tenant_enum_and_comment
Revises: 004_plugin_definition_fields
Create Date: 2026-06-29

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_tenant_enum_and_comment"
down_revision: str | None = "004_plugin_definition_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    # 添加表级 comment
    op.execute("COMMENT ON TABLE tenant.tenants IS '租户表'")
    op.execute("COMMENT ON TABLE tenant.tenant_admins IS '租户管理员表'")
    op.execute("COMMENT ON TABLE tenant.plugin_installations IS '插件安装记录表'")
    op.execute("COMMENT ON TABLE tenant.plugin_definitions IS '插件定义表'")
    op.execute("COMMENT ON TABLE tenant.modules IS '模块定义表'")
    op.execute("COMMENT ON TABLE tenant.module_permissions IS '模块权限表'")
    op.execute("COMMENT ON TABLE tenant.module_roles IS '模块角色表'")
    op.execute("COMMENT ON TABLE tenant.tenant_modules IS '租户模块分配表'")
    op.execute("COMMENT ON TABLE tenant.module_menus IS '模块菜单定义表'")
    op.execute("COMMENT ON TABLE tenant.module_menu_permissions IS '模块菜单-权限关联表'")
    op.execute("COMMENT ON TABLE tenant.module_role_permissions IS '模块角色-权限关联表'")
    op.execute("COMMENT ON TABLE tenant.cache_configs IS '缓存配置表'")
    op.execute("COMMENT ON TABLE tenant.database_configs IS '数据库配置表'")
    op.execute("COMMENT ON TABLE tenant.pubsub_configs IS '发布订阅配置表'")
    op.execute("COMMENT ON TABLE tenant.queue_configs IS '队列配置表'")
    op.execute("COMMENT ON TABLE tenant.storage_configs IS '存储配置表'")
    op.execute("COMMENT ON TABLE tenant.tenant_configs IS '租户配置表'")
    op.execute("COMMENT ON TABLE tenant.tenant_business_configs IS '租户业务配置表'")


def downgrade() -> None:
    # 移除表级 comment
    op.execute("COMMENT ON TABLE tenant.tenants IS NULL")
    op.execute("COMMENT ON TABLE tenant.tenant_admins IS NULL")
    op.execute("COMMENT ON TABLE tenant.plugin_installations IS NULL")
    op.execute("COMMENT ON TABLE tenant.plugin_definitions IS NULL")
    op.execute("COMMENT ON TABLE tenant.modules IS NULL")
    op.execute("COMMENT ON TABLE tenant.module_permissions IS NULL")
    op.execute("COMMENT ON TABLE tenant.module_roles IS NULL")
    op.execute("COMMENT ON TABLE tenant.tenant_modules IS NULL")
    op.execute("COMMENT ON TABLE tenant.module_menus IS NULL")
    op.execute("COMMENT ON TABLE tenant.module_menu_permissions IS NULL")
    op.execute("COMMENT ON TABLE tenant.module_role_permissions IS NULL")
    op.execute("COMMENT ON TABLE tenant.cache_configs IS NULL")
    op.execute("COMMENT ON TABLE tenant.database_configs IS NULL")
    op.execute("COMMENT ON TABLE tenant.pubsub_configs IS NULL")
    op.execute("COMMENT ON TABLE tenant.queue_configs IS NULL")
    op.execute("COMMENT ON TABLE tenant.storage_configs IS NULL")
    op.execute("COMMENT ON TABLE tenant.tenant_configs IS NULL")
    op.execute("COMMENT ON TABLE tenant.tenant_business_configs IS NULL")

