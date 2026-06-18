"""更新菜单路径，将 resource-configs 改回 resources

Revision ID: 007_menu_paths_resources
Revises: 003_tenant_resource_ref
Create Date: 2026-06-18

更新内容：
- tenant.module_menus 表：更新 tenant.resources 菜单的 path 字段
- iam.menus 表：更新 tenant.resources 菜单的 path 字段

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "007_menu_paths_resources"
down_revision: Union[str, None] = "004_resource_default"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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
