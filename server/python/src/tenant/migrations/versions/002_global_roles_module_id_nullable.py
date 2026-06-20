"""全局角色支持：module_id 可为 NULL

Revision ID: 002_global_roles
Revises: 001_tenant_initial
Create Date: 2026-06-20

将 module_roles.module_id 改为可空，以支持全局角色（module_id=NULL）。
添加部分唯一索引，确保全局角色的 code 唯一。

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_global_roles"
down_revision: str | None = "001_tenant_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "tenant"


def upgrade() -> None:
    # 1. 将 module_roles.module_id 改为可空
    op.alter_column(
        "module_roles",
        "module_id",
        existing_type=sa.String(36),
        nullable=True,
        comment="模块ID（NULL 表示全局角色）",
        schema=MODULE_SCHEMA,
    )

    # 2. 添加部分唯一索引：当 module_id 为 NULL 时，code 必须唯一
    op.execute(
        f"""
        CREATE UNIQUE INDEX uq_module_roles_global_code
        ON {MODULE_SCHEMA}.module_roles (code)
        WHERE module_id IS NULL
        """
    )


def downgrade() -> None:
    # 1. 删除部分唯一索引
    op.execute(f"DROP INDEX IF EXISTS {MODULE_SCHEMA}.uq_module_roles_global_code")

    # 2. 将 module_roles.module_id 改回不可空
    # 注意：降级前需确保没有 module_id 为 NULL 的记录
    op.alter_column(
        "module_roles",
        "module_id",
        existing_type=sa.String(36),
        nullable=False,
        comment="模块ID",
        schema=MODULE_SCHEMA,
    )
