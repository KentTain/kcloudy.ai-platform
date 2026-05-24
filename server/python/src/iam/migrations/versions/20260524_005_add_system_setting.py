"""add system_settings and system_setting_attributes tables

Revision ID: 005_system_setting
Revises: 004_tree
Create Date: 2026-05-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_system_setting"
down_revision: Union[str, None] = "004_tree"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 system_settings 表
    op.create_table(
        "system_settings",
        sa.Column("id", sa.String(36), primary_key=True, comment="ID"),
        sa.Column("tenant_id", sa.String(32), nullable=False, comment="租户ID"),
        sa.Column("code", sa.String(20), nullable=False, comment="设置编号"),
        sa.Column("name", sa.String(256), nullable=False, comment="名称"),
        sa.Column("display_name", sa.String(512), nullable=True, comment="显示名称"),
        sa.Column("description", sa.String(4000), nullable=True, comment="描述"),
        sa.Column("application_id", sa.String(36), nullable=True, comment="应用程序Id"),
        sa.Column("application_name", sa.String(128), nullable=True, comment="应用程序名称"),
        sa.Column("can_edit", sa.Boolean, nullable=False, server_default="true", comment="是否能编辑"),
        sa.Column("is_require", sa.Boolean, nullable=False, server_default="false", comment="是否必须"),
        sa.Column("index", sa.Integer, nullable=False, server_default="0", comment="排序"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
    )

    # 创建 system_settings 索引
    op.create_index("ix_system_settings_tenant_id", "system_settings", ["tenant_id"])
    op.create_index("uq_system_settings_tenant_code", "system_settings", ["tenant_id", "code"], unique=True)

    # 创建 system_setting_attributes 表
    op.create_table(
        "system_setting_attributes",
        sa.Column("id", sa.String(36), primary_key=True, comment="ID"),
        sa.Column("tenant_id", sa.String(32), nullable=False, comment="租户ID"),
        sa.Column("setting_id", sa.String(36), sa.ForeignKey("system_settings.id", ondelete="CASCADE"), nullable=False, comment="配置Id"),
        sa.Column("data_type", sa.String(20), nullable=False, server_default="string", comment="属性数据类型"),
        sa.Column("name", sa.String(256), nullable=False, comment="属性值名称"),
        sa.Column("display_name", sa.String(512), nullable=True, comment="显示名称"),
        sa.Column("description", sa.String(4000), nullable=True, comment="描述"),
        sa.Column("value", sa.Text, nullable=True, comment="属性值"),
        sa.Column("ext_data", postgresql.JSONB, nullable=True, comment="扩展数据"),
        sa.Column("can_edit", sa.Boolean, nullable=False, server_default="true", comment="是否能编辑"),
        sa.Column("is_require", sa.Boolean, nullable=False, server_default="false", comment="是否必须"),
        sa.Column("index", sa.Integer, nullable=False, server_default="0", comment="排序"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment="更新时间"),
    )

    # 创建 system_setting_attributes 索引
    op.create_index("ix_system_setting_attributes_tenant_id", "system_setting_attributes", ["tenant_id"])
    op.create_index("ix_system_setting_attributes_setting_id", "system_setting_attributes", ["setting_id"])
    op.create_index("uq_system_setting_attributes_setting_name", "system_setting_attributes", ["setting_id", "name"], unique=True)


def downgrade() -> None:
    # 删除 system_setting_attributes 表
    op.drop_index("uq_system_setting_attributes_setting_name", table_name="system_setting_attributes")
    op.drop_index("ix_system_setting_attributes_setting_id", table_name="system_setting_attributes")
    op.drop_index("ix_system_setting_attributes_tenant_id", table_name="system_setting_attributes")
    op.drop_table("system_setting_attributes")

    # 删除 system_settings 表
    op.drop_index("uq_system_settings_tenant_code", table_name="system_settings")
    op.drop_index("ix_system_settings_tenant_id", table_name="system_settings")
    op.drop_table("system_settings")
