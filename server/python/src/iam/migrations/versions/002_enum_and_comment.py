"""补充表级comment并将字段从String改为EnumType

Revision ID: 002_iam_enum_and_comment
Revises: 001_iam_initial
Create Date: 2026-06-29

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_iam_enum_and_comment"
down_revision: str | None = "001_iam_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "iam"


def upgrade() -> None:
    # 添加表级 comment
    op.execute("COMMENT ON TABLE iam.users IS '用户表'")
    op.execute("COMMENT ON TABLE iam.roles IS '角色表'")
    op.execute("COMMENT ON TABLE iam.permissions IS '权限表'")
    op.execute("COMMENT ON TABLE iam.organizations IS '组织表'")
    op.execute("COMMENT ON TABLE iam.user_organizations IS '用户组织关联表'")
    op.execute("COMMENT ON TABLE iam.user_roles IS '用户角色关联表'")
    op.execute("COMMENT ON TABLE iam.role_permissions IS '角色权限关联表'")
    op.execute("COMMENT ON TABLE iam.user_tenants IS '用户租户关联表'")
    op.execute("COMMENT ON TABLE iam.oauth_connections IS 'OAuth关联表'")
    op.execute("COMMENT ON TABLE iam.system_settings IS '系统设置表'")
    op.execute("COMMENT ON TABLE iam.system_setting_attributes IS '系统设置属性表'")
    op.execute("COMMENT ON TABLE iam.menus IS '菜单表'")
    op.execute("COMMENT ON TABLE iam.menu_permissions IS '菜单权限关联表'")


def downgrade() -> None:
    # 移除表级 comment
    op.execute("COMMENT ON TABLE iam.users IS NULL")
    op.execute("COMMENT ON TABLE iam.roles IS NULL")
    op.execute("COMMENT ON TABLE iam.permissions IS NULL")
    op.execute("COMMENT ON TABLE iam.organizations IS NULL")
    op.execute("COMMENT ON TABLE iam.user_organizations IS NULL")
    op.execute("COMMENT ON TABLE iam.user_roles IS NULL")
    op.execute("COMMENT ON TABLE iam.role_permissions IS NULL")
    op.execute("COMMENT ON TABLE iam.user_tenants IS NULL")
    op.execute("COMMENT ON TABLE iam.oauth_connections IS NULL")
    op.execute("COMMENT ON TABLE iam.system_settings IS NULL")
    op.execute("COMMENT ON TABLE iam.system_setting_attributes IS NULL")
    op.execute("COMMENT ON TABLE iam.menus IS NULL")
    op.execute("COMMENT ON TABLE iam.menu_permissions IS NULL")
