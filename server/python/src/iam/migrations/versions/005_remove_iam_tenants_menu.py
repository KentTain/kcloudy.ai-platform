"""remove iam.tenants menu from all tenants

Revision ID: 005_remove_iam_tenants_menu
Revises: 004_iam_module_sync
Create Date: 2026-06-15

清理错误定义的 iam.tenants 菜单和权限：
- 从 module_menus 表删除 iam.tenants 菜单定义
- 从所有租户的 menus 表删除 iam.tenants 菜单实例
- 从所有租户的 permissions 表删除 iam:tenant:* 权限实例
- 从所有租户的 role_permissions 表删除相关关联

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_remove_iam_tenants_menu"
down_revision: str | None = "004_iam_module_sync"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    清理错误的 iam.tenants 菜单和权限定义

    注意：这个迁移不可逆，因为这些数据本身就是错误的
    """
    # 获取数据库连接
    conn = op.get_bind()

    # 1. 从 module_menus 表删除 iam.tenants 菜单定义
    conn.execute(
        sa.text("""
            DELETE FROM tenant.module_menus
            WHERE code = 'iam.tenants'
        """)
    )

    # 2. 从所有租户的 menus 表删除 iam.tenants 菜单实例
    conn.execute(
        sa.text("""
            DELETE FROM iam.menus
            WHERE code = 'iam.tenants'
        """)
    )

    # 3. 从 module_permissions 表删除 iam:tenant:* 权限定义
    conn.execute(
        sa.text("""
            DELETE FROM tenant.module_permissions
            WHERE code LIKE 'iam:tenant:%'
        """)
    )

    # 4. 从所有租户的 permissions 表删除 iam:tenant:* 权限实例
    conn.execute(
        sa.text("""
            DELETE FROM iam.permissions
            WHERE code LIKE 'iam:tenant:%'
        """)
    )

    # 5. 删除相关的 menu_permissions 关联
    # (由于菜单已删除，级联删除会自动处理，但为了明确性显式执行)
    conn.execute(
        sa.text("""
            DELETE FROM iam.menu_permissions
            WHERE menu_id IN (
                SELECT id FROM iam.menus WHERE code = 'iam.tenants'
            )
        """)
    )

    # 6. 删除相关的 role_permissions 关联
    conn.execute(
        sa.text("""
            DELETE FROM iam.role_permissions
            WHERE permission_id IN (
                SELECT id FROM iam.permissions WHERE code LIKE 'iam:tenant:%'
            )
        """)
    )


def downgrade() -> None:
    """
    回滚操作：不恢复错误数据

    这些数据本身就是错误的定义，不应该恢复
    """
    pass
