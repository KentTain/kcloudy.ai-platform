"""审计日志表创建和字段类型调整

Revision ID: 003_audit_log
Revises: 002_iam_enum_and_comment
Create Date: 2026-07-01

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "003_audit_log"
down_revision = "002_iam_enum_and_comment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库"""

    # 检查表是否存在
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'iam'
            AND table_name = 'audit_log'
        )
    """))
    table_exists = result.scalar()

    if not table_exists:
        # 表不存在，直接创建新表（使用字符串类型字段）
        op.execute("""
            CREATE TABLE iam.audit_log (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                tenant_id VARCHAR(36) NOT NULL,
                business_domain VARCHAR(64) NOT NULL,
                business_domain_id VARCHAR(64),
                permission_code VARCHAR(128),
                operator_by VARCHAR(36) NOT NULL,
                operator_name VARCHAR(256) NOT NULL,
                operated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                operation_type VARCHAR(64) NOT NULL,
                resource_type VARCHAR(64) NOT NULL,
                resource_id VARCHAR(64),
                resource_name VARCHAR(256) NOT NULL,
                before_data JSONB,
                after_data JSONB,
                detail JSONB,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR(36),
                updated_by VARCHAR(36)
            )
        """)

        # 创建索引
        op.execute("CREATE INDEX ix_audit_log_tenant_id ON iam.audit_log(tenant_id)")
        op.execute("CREATE INDEX ix_audit_log_business_domain ON iam.audit_log(business_domain)")
        op.execute("CREATE INDEX ix_audit_log_business_domain_id ON iam.audit_log(business_domain_id)")
        op.execute("CREATE INDEX ix_audit_log_permission_code ON iam.audit_log(permission_code)")
        op.execute("CREATE INDEX ix_audit_log_operator_by ON iam.audit_log(operator_by)")
        op.execute("CREATE INDEX ix_audit_log_operated_at ON iam.audit_log(operated_at)")
        op.execute("CREATE INDEX ix_audit_log_resource_id ON iam.audit_log(resource_id)")

        # 添加表注释
        op.execute("COMMENT ON TABLE iam.audit_log IS '审计日志表'")
        op.execute("COMMENT ON COLUMN iam.audit_log.business_domain IS '业务域（模块名称）'")
        op.execute("COMMENT ON COLUMN iam.audit_log.business_domain_id IS '业务域ID'")
        op.execute("COMMENT ON COLUMN iam.audit_log.permission_code IS '权限编码'")
        op.execute("COMMENT ON COLUMN iam.audit_log.operator_by IS '操作用户ID'")
        op.execute("COMMENT ON COLUMN iam.audit_log.operator_name IS '操作用户名'")
        op.execute("COMMENT ON COLUMN iam.audit_log.operated_at IS '操作时间'")
        op.execute("COMMENT ON COLUMN iam.audit_log.operation_type IS '操作类型'")
        op.execute("COMMENT ON COLUMN iam.audit_log.resource_type IS '资源类型'")
        op.execute("COMMENT ON COLUMN iam.audit_log.resource_id IS '主操作对象ID'")
        op.execute("COMMENT ON COLUMN iam.audit_log.resource_name IS '主操作对象名称'")
        op.execute("COMMENT ON COLUMN iam.audit_log.before_data IS '操作前数据'")
        op.execute("COMMENT ON COLUMN iam.audit_log.after_data IS '操作后数据'")
        op.execute("COMMENT ON COLUMN iam.audit_log.detail IS '操作详情'")

    else:
        # 表已存在，执行字段类型转换
        # 检查是否有 details 字段需要重命名
        result = conn.execute(sa.text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'iam'
            AND table_name = 'audit_log'
            AND column_name = 'details'
        """))
        has_details = result.fetchone()

        if has_details:
            # 重命名字段
            op.execute("ALTER TABLE iam.audit_log RENAME COLUMN details TO detail")

        # 检查是否需要添加 permission_code 字段
        result = conn.execute(sa.text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'iam'
            AND table_name = 'audit_log'
            AND column_name = 'permission_code'
        """))
        has_permission_code = result.fetchone()

        if not has_permission_code:
            # 添加 permission_code 字段
            op.execute("""
                ALTER TABLE iam.audit_log
                ADD COLUMN permission_code VARCHAR(128)
            """)
            op.execute("CREATE INDEX ix_audit_log_permission_code ON iam.audit_log(permission_code)")
            op.execute("COMMENT ON COLUMN iam.audit_log.permission_code IS '权限编码'")

        # 转换枚举字段为字符串（保留数据）
        # 检查字段类型
        result = conn.execute(sa.text("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = 'iam'
            AND table_name = 'audit_log'
            AND column_name = 'business_domain'
        """))
        row = result.fetchone()
        if row and row[0] == 'USER-DEFINED':
            # 枚举类型，需要转换
            op.execute("""
                ALTER TABLE iam.audit_log
                ALTER COLUMN business_domain TYPE VARCHAR(64)
                USING business_domain::text
            """)
            op.execute("""
                ALTER TABLE iam.audit_log
                ALTER COLUMN operation_type TYPE VARCHAR(64)
                USING operation_type::text
            """)
            op.execute("""
                ALTER TABLE iam.audit_log
                ALTER COLUMN resource_type TYPE VARCHAR(64)
                USING resource_type::text
            """)

            # 删除枚举类型
            op.execute("DROP TYPE IF EXISTS iam.auditlogbusinesstype")
            op.execute("DROP TYPE IF EXISTS iam.auditlogoperationtype")
            op.execute("DROP TYPE IF EXISTS iam.auditlogresourcetype")


def downgrade() -> None:
    """回滚数据库"""

    # 删除表
    op.execute("DROP TABLE IF EXISTS iam.audit_log")

    # 删除枚举类型（如果存在）
    op.execute("DROP TYPE IF EXISTS iam.auditlogbusinesstype")
    op.execute("DROP TYPE IF EXISTS iam.auditlogoperationtype")
    op.execute("DROP TYPE IF EXISTS iam.auditlogresourcetype")
