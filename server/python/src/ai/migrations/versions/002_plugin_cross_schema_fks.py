"""add plugin cross schema foreign keys

Revision ID: 002_plugin_fks
Revises: 001_plugin
Create Date: 2026-06-02

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_plugin_fks"
down_revision: Union[str, None] = "001_plugin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 模块 schema
MODULE_SCHEMA = "ai"


def upgrade() -> None:
    # plugin_installations.tenant_id -> tenant.tenants.id
    op.create_foreign_key(
        constraint_name="fk_plugin_installations_tenant_id",
        source_table="plugin_installations",
        referent_table="tenants",
        local_cols=["tenant_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="tenant",
        ondelete="CASCADE",
    )

    # plugin_installations.created_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_plugin_installations_created_by",
        source_table="plugin_installations",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugin_installations.updated_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_plugin_installations_updated_by",
        source_table="plugin_installations",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugin_install_tasks.tenant_id -> tenant.tenants.id
    op.create_foreign_key(
        constraint_name="fk_plugin_install_tasks_tenant_id",
        source_table="plugin_install_tasks",
        referent_table="tenants",
        local_cols=["tenant_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="tenant",
        ondelete="CASCADE",
    )

    # plugin_install_tasks.created_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_plugin_install_tasks_created_by",
        source_table="plugin_install_tasks",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugin_install_tasks.updated_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_plugin_install_tasks_updated_by",
        source_table="plugin_install_tasks",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugin_credentials.tenant_id -> tenant.tenants.id
    op.create_foreign_key(
        constraint_name="fk_plugin_credentials_tenant_id",
        source_table="plugin_credentials",
        referent_table="tenants",
        local_cols=["tenant_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="tenant",
        ondelete="CASCADE",
    )

    # plugin_credentials.created_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_plugin_credentials_created_by",
        source_table="plugin_credentials",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugin_credentials.updated_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_plugin_credentials_updated_by",
        source_table="plugin_credentials",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugins.created_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_plugins_created_by",
        source_table="plugins",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugins.updated_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_plugins_updated_by",
        source_table="plugins",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugin_declarations.created_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_plugin_declarations_created_by",
        source_table="plugin_declarations",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # plugin_declarations.updated_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_plugin_declarations_updated_by",
        source_table="plugin_declarations",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # plugin_declarations
    op.drop_constraint("fk_plugin_declarations_updated_by", "plugin_declarations", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_plugin_declarations_created_by", "plugin_declarations", schema=MODULE_SCHEMA, type_="foreignkey")

    # plugins
    op.drop_constraint("fk_plugins_updated_by", "plugins", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_plugins_created_by", "plugins", schema=MODULE_SCHEMA, type_="foreignkey")

    # plugin_credentials
    op.drop_constraint("fk_plugin_credentials_updated_by", "plugin_credentials", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_plugin_credentials_created_by", "plugin_credentials", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_plugin_credentials_tenant_id", "plugin_credentials", schema=MODULE_SCHEMA, type_="foreignkey")

    # plugin_install_tasks
    op.drop_constraint("fk_plugin_install_tasks_updated_by", "plugin_install_tasks", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_plugin_install_tasks_created_by", "plugin_install_tasks", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_plugin_install_tasks_tenant_id", "plugin_install_tasks", schema=MODULE_SCHEMA, type_="foreignkey")

    # plugin_installations
    op.drop_constraint("fk_plugin_installations_updated_by", "plugin_installations", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_plugin_installations_created_by", "plugin_installations", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_plugin_installations_tenant_id", "plugin_installations", schema=MODULE_SCHEMA, type_="foreignkey")
