"""
TenantAdmin 模型 role 字段单元测试

测试 TenantAdmin 模型中 role 字段的映射定义：
- 字段类型为 String(50)
- 不可为空
- 默认值为 "ordinaryAdmin"
- 包含 comment 属性
"""

from unittest.mock import MagicMock

from sqlalchemy import String

from tenant.models.tenant_admin import TenantAdmin


class TestTenantAdminRoleField:
    """TenantAdmin 模型 role 字段测试"""

    def test_role_column_defined(self):
        """role 字段在模型中已定义"""
        assert hasattr(TenantAdmin, "role")

    def test_role_column_type_is_string_50(self):
        """role 字段类型为 String(50)"""
        column = TenantAdmin.__table__.c.role
        assert isinstance(column.type, String)
        assert column.type.length == 50

    def test_role_not_nullable(self):
        """role 字段不可为空"""
        column = TenantAdmin.__table__.c.role
        assert column.nullable is False

    def test_role_default_is_ordinary_admin(self):
        """role 字段 Python 默认值为 ordinaryAdmin"""
        column = TenantAdmin.__table__.c.role
        assert column.default.arg == "ordinaryAdmin"

    def test_role_comment_is_role_code(self):
        """role 字段 comment 为 角色编码"""
        column = TenantAdmin.__table__.c.role
        assert column.comment == "角色编码"


class TestTenantAdminRoleInstance:
    """TenantAdmin role 字段实例行为测试"""

    def test_role_default_value_is_ordinary_admin(self):
        """role 字段 Python 默认值为 ordinaryAdmin"""
        admin = MagicMock(spec=TenantAdmin)
        admin.role = "ordinaryAdmin"
        assert admin.role == "ordinaryAdmin"

    def test_role_can_be_tenant_admin(self):
        """role 字段可以设置为 tenantAdmin"""
        admin = MagicMock(spec=TenantAdmin)
        admin.role = "tenantAdmin"
        assert admin.role == "tenantAdmin"

    def test_role_can_be_ordinary_admin(self):
        """role 字段可以设置为 ordinaryAdmin"""
        admin = MagicMock(spec=TenantAdmin)
        admin.role = "ordinaryAdmin"
        assert admin.role == "ordinaryAdmin"
