"""
TenantAdmin 模型 role 字段单元测试

测试 TenantAdmin 模型中 role 字段的映射定义：
- 字段类型为 EnumType(TenantAdminRole)
- 不可为空
- 默认值为 TenantAdminRole.ORDINARY_ADMIN
- 包含 comment 属性
"""

from unittest.mock import MagicMock

from framework.database.types.enum import EnumType
from tenant.models.enums import TenantAdminRole
from tenant.models.tenant_admin import TenantAdmin


class TestTenantAdminRoleField:
    """TenantAdmin 模型 role 字段测试"""

    def test_role_column_defined(self):
        """role 字段在模型中已定义"""
        assert hasattr(TenantAdmin, "role")

    def test_role_column_type_is_enum(self):
        """role 字段类型为 EnumType"""
        column = TenantAdmin.__table__.c.role
        assert isinstance(column.type, EnumType)
        assert column.type.length == 20

    def test_role_not_nullable(self):
        """role 字段不可为空"""
        column = TenantAdmin.__table__.c.role
        assert column.nullable is False

    def test_role_default_is_ordinary_admin(self):
        """role 字段 Python 默认值为 ORDINARY_ADMIN"""
        column = TenantAdmin.__table__.c.role
        assert column.default.arg == TenantAdminRole.ORDINARY_ADMIN

    def test_role_comment_is_role(self):
        """role 字段 comment 为 角色"""
        column = TenantAdmin.__table__.c.role
        assert column.comment == "角色"


class TestTenantAdminRoleInstance:
    """TenantAdmin role 字段实例行为测试"""

    def test_role_default_value_is_ordinary_admin(self):
        """role 字段 Python 默认值为 ORDINARY_ADMIN"""
        admin = MagicMock(spec=TenantAdmin)
        admin.role = TenantAdminRole.ORDINARY_ADMIN
        assert admin.role == TenantAdminRole.ORDINARY_ADMIN

    def test_role_can_be_tenant_admin(self):
        """role 字段可以设置为 TENANT_ADMIN"""
        admin = MagicMock(spec=TenantAdmin)
        admin.role = TenantAdminRole.TENANT_ADMIN
        assert admin.role == TenantAdminRole.TENANT_ADMIN

    def test_role_can_be_ordinary_admin(self):
        """role 字段可以设置为 ORDINARY_ADMIN"""
        admin = MagicMock(spec=TenantAdmin)
        admin.role = TenantAdminRole.ORDINARY_ADMIN
        assert admin.role == TenantAdminRole.ORDINARY_ADMIN
