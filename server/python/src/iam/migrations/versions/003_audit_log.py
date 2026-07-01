"""审计日志字段类型调整

Revision ID: 003_audit_log
Revises: 002_initial
Create Date: 2026-07-01

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003_audit_log"
down_revision = "002_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库"""

    # 1. 删除旧字段（枚举类型）
    op.drop_column("audit_log", "business_domain", schema="iam")
    op.drop_column("audit_log", "operation_type", schema="iam")
    op.drop_column("audit_log", "resource_type", schema="iam")

    # 2. 添加新字段（字符串类型）
    op.add_column(
        "audit_log",
        sa.Column(
            "business_domain",
            sa.String(64),
            nullable=False,
            comment="业务域（模块名称）",
        ),
        schema="iam",
    )
    op.add_column(
        "audit_log",
        sa.Column(
            "operation_type",
            sa.String(64),
            nullable=False,
            comment="操作类型",
        ),
        schema="iam",
    )
    op.add_column(
        "audit_log",
        sa.Column(
            "resource_type",
            sa.String(64),
            nullable=False,
            comment="资源类型",
        ),
        schema="iam",
    )

    # 3. 添加新字段
    op.add_column(
        "audit_log",
        sa.Column(
            "permission_code",
            sa.String(128),
            nullable=True,
            comment="权限编码",
        ),
        schema="iam",
    )

    # 4. 重命名字段
    op.alter_column("audit_log", "details", new_column_name="detail", schema="iam")

    # 5. 创建索引
    op.create_index(
        "ix_audit_log_permission_code",
        "audit_log",
        ["permission_code"],
        schema="iam",
    )

    # 6. 删除枚举类型
    op.execute("DROP TYPE IF EXISTS iam.auditlogbusinesstype")
    op.execute("DROP TYPE IF EXISTS iam.auditlogoperationtype")
    op.execute("DROP TYPE IF EXISTS iam.auditlogresourcetype")


def downgrade() -> None:
    """回滚数据库"""

    # 1. 删除索引
    op.drop_index("ix_audit_log_permission_code", table_name="audit_log", schema="iam")

    # 2. 删除新字段
    op.drop_column("audit_log", "permission_code", schema="iam")

    # 3. 重命名字段回退
    op.alter_column("audit_log", "detail", new_column_name="details", schema="iam")

    # 4. 删除字符串字段
    op.drop_column("audit_log", "business_domain", schema="iam")
    op.drop_column("audit_log", "operation_type", schema="iam")
    op.drop_column("audit_log", "resource_type", schema="iam")

    # 5. 创建枚举类型
    op.execute(
        "CREATE TYPE iam.auditlogbusinesstype AS ENUM ('library', 'knowledge_base', 'tag', 'role', 'system_role', 'user', 'dept', 'platform_setting')"
    )
    op.execute(
        "CREATE TYPE iam.auditlogoperationtype AS ENUM ('library.library_create', 'user.user_create')"
    )
    op.execute(
        "CREATE TYPE iam.auditlogresourcetype AS ENUM ('user', 'dept', 'role', 'system_role', 'tag', 'library')"
    )

    # 6. 添加枚举字段
    op.add_column(
        "audit_log",
        sa.Column(
            "business_domain",
            sa.Enum(
                "library",
                "knowledge_base",
                "tag",
                "role",
                "system_role",
                "user",
                "dept",
                "platform_setting",
                name="auditlogbusinesstype",
                schema="iam",
            ),
            nullable=False,
        ),
        schema="iam",
    )
    op.add_column(
        "audit_log",
        sa.Column(
            "operation_type",
            sa.Enum(
                "library.library_create",
                "user.user_create",
                name="auditlogoperationtype",
                schema="iam",
            ),
            nullable=False,
        ),
        schema="iam",
    )
    op.add_column(
        "audit_log",
        sa.Column(
            "resource_type",
            sa.Enum(
                "user",
                "dept",
                "role",
                "system_role",
                "tag",
                "library",
                name="auditlogresourcetype",
                schema="iam",
            ),
            nullable=False,
        ),
        schema="iam",
    )
