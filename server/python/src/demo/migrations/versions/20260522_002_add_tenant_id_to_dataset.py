"""add tenant id to dataset

Revision ID: demo_002_tenant_dataset
Revises:
Create Date: 2026-05-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "demo_002_tenant_dataset"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "dataset",
        sa.Column(
            "tenant_id",
            sa.String(32),
            nullable=False,
            server_default="00000000-0000-0000-0000-000000000000",
            comment="租户ID",
        ),
    )
    op.create_index("ix_dataset_tenant_id", "dataset", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_dataset_tenant_id", table_name="dataset")
    op.drop_column("dataset", "tenant_id")
