"""更新菜单路径以匹配统一 API 路由规范

Revision ID: 007_menu_paths_resources
Revises: 006_update_menu_paths
Create Date: 2026-06-17

更新内容：
- tenant.module_menus 表：更新 tenant.resources 菜单的 path 字段
- iam.menus 表：更新 tenant.resources 菜单的 path 字段

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "007_menu_paths_resources"
down_revision: str | None = "006_update_menu_paths"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """更新菜单路径"""

    # 1. 更新 tenant.module_menus 表
    op.execute(
        text("""
            UPDATE tenant.module_menus
            SET path = '/admin/resources'
            WHERE code = 'tenant.resources' AND path = '/admin/resource-configs'
        """)
    )

    # 2. 更新 iam.menus 表
    op.execute(
        text("""
            UPDATE iam.menus
            SET path = '/admin/resources'
            WHERE code = 'tenant.resources' AND path = '/admin/resource-configs'
        """)
    )


def downgrade() -> None:
    """回滚菜单路径更新"""

    # 1. 回滚 tenant.module_menus 表
    op.execute(
        text("""
            UPDATE tenant.module_menus
            SET path = '/admin/resource-configs'
            WHERE code = 'tenant.resources' AND path = '/admin/resources'
        """)
    )

    # 2. 回滚 iam.menus 表
    op.execute(
        text("""
            UPDATE iam.menus
            SET path = '/admin/resource-configs'
            WHERE code = 'tenant.resources' AND path = '/admin/resources'
        """)
    )
