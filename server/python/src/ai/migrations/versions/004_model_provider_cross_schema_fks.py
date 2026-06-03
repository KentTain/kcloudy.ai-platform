"""add model provider cross schema foreign keys

Revision ID: 004_model_provider_fks
Revises: 003_model_provider
Create Date: 2026-06-03

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_model_provider_fks"
down_revision: Union[str, None] = "003_model_provider"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 模块 schema
MODULE_SCHEMA = "ai"


def upgrade() -> None:
    # model_providers.tenant_id -> tenant.tenants.id
    op.create_foreign_key(
        constraint_name="fk_model_providers_tenant_id",
        source_table="model_providers",
        referent_table="tenants",
        local_cols=["tenant_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="tenant",
        ondelete="CASCADE",
    )

    # model_providers.created_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_model_providers_created_by",
        source_table="model_providers",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # model_providers.updated_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_model_providers_updated_by",
        source_table="model_providers",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # model_configs.tenant_id -> tenant.tenants.id
    op.create_foreign_key(
        constraint_name="fk_model_configs_tenant_id",
        source_table="model_configs",
        referent_table="tenants",
        local_cols=["tenant_id"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="tenant",
        ondelete="CASCADE",
    )

    # model_configs.created_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_model_configs_created_by",
        source_table="model_configs",
        referent_table="users",
        local_cols=["created_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )

    # model_configs.updated_by -> iam.users.id
    op.create_foreign_key(
        constraint_name="fk_model_configs_updated_by",
        source_table="model_configs",
        referent_table="users",
        local_cols=["updated_by"],
        remote_cols=["id"],
        source_schema=MODULE_SCHEMA,
        referent_schema="iam",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # model_configs
    op.drop_constraint("fk_model_configs_updated_by", "model_configs", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_model_configs_created_by", "model_configs", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_model_configs_tenant_id", "model_configs", schema=MODULE_SCHEMA, type_="foreignkey")

    # model_providers
    op.drop_constraint("fk_model_providers_updated_by", "model_providers", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_model_providers_created_by", "model_providers", schema=MODULE_SCHEMA, type_="foreignkey")
    op.drop_constraint("fk_model_providers_tenant_id", "model_providers", schema=MODULE_SCHEMA, type_="foreignkey")
