"""修复 user_tenants 表的 is_default 字段

为每个用户的第一个租户设置 is_default=True

Revision ID: fix_user_tenant_default
Revises:
Create Date: 2025-01-05

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "fix_user_tenant_default"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """修复 user_tenants 表的 is_default 字段"""
    # 为每个用户设置第一个租户为默认租户
    op.execute("""
        UPDATE iam.user_tenants
        SET is_default = true
        WHERE id IN (
            SELECT DISTINCT ON (user_id) id
            FROM iam.user_tenants
            ORDER BY user_id, created_at
        )
    """)


def downgrade() -> None:
    """回滚：将所有 is_default 设置为 false"""
    op.execute("UPDATE iam.user_tenants SET is_default = false")
