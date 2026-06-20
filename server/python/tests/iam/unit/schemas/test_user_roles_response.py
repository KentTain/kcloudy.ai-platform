"""测试 IAM 模块 Schema 转换方法

测试 UserRoleItem、UserRolesResponse、OrganizationListItem、OrganizationListResponse 转换方法。
"""

from unittest.mock import MagicMock


class TestUserRoleItem:
    """测试 UserRoleItem Schema"""

    def test_from_role_basic_fields(self):
        """测试 from_role() 方法基础字段映射"""
        from iam.schemas.user import UserRoleItem

        # 创建 mock Role 对象
        role = MagicMock()
        role.id = "role-123"
        role.code = "admin"
        role.name = "管理员"
        role.description = "系统管理员角色"

        result = UserRoleItem.from_role(role)

        assert result.id == "role-123"
        assert result.code == "admin"
        assert result.name == "管理员"
        assert result.description == "系统管理员角色"

    def test_from_role_null_description(self):
        """测试 from_role() 方法处理空描述"""
        from iam.schemas.user import UserRoleItem

        role = MagicMock()
        role.id = "role-456"
        role.code = "viewer"
        role.name = "查看者"
        role.description = None

        result = UserRoleItem.from_role(role)

        assert result.description is None


class TestUserRolesResponse:
    """测试 UserRolesResponse Schema"""

    def test_from_roles_empty_list(self):
        """测试 from_roles() 方法处理空列表"""
        from iam.schemas.user import UserRolesResponse

        result = UserRolesResponse.from_roles([])

        assert result.roles == []

    def test_from_roles_multiple_roles(self):
        """测试 from_roles() 方法处理多个角色"""
        from iam.schemas.user import UserRolesResponse

        # 创建多个 mock Role 对象
        role1 = MagicMock()
        role1.id = "role-1"
        role1.code = "admin"
        role1.name = "管理员"
        role1.description = "管理员角色"

        role2 = MagicMock()
        role2.id = "role-2"
        role2.code = "editor"
        role2.name = "编辑者"
        role2.description = "编辑者角色"

        result = UserRolesResponse.from_roles([role1, role2])

        assert len(result.roles) == 2
        assert result.roles[0].code == "admin"
        assert result.roles[1].code == "editor"


class TestOrganizationListItem:
    """测试 OrganizationListItem Schema"""

    def test_from_organization_basic_fields(self):
        """测试 from_organization() 方法基础字段映射"""
        from iam.schemas.organization import OrganizationListItem

        # 创建 mock Organization 对象
        org = MagicMock()
        org.id = "org-123"
        org.name = "技术部"
        org.code = "tech"
        org.parent_id = None
        org.sort_order = 1
        org.leader_id = "user-456"
        org.status = "active"

        result = OrganizationListItem.from_organization(org)

        assert result.id == "org-123"
        assert result.name == "技术部"
        assert result.code == "tech"
        assert result.parent_id is None
        assert result.sort_order == 1
        assert result.leader_id == "user-456"
        assert result.status == "active"

    def test_from_organization_null_fields(self):
        """测试 from_organization() 方法处理空字段"""
        from iam.schemas.organization import OrganizationListItem

        org = MagicMock()
        org.id = "org-456"
        org.name = "新组织"
        org.code = None
        org.parent_id = "org-123"
        org.sort_order = 0
        org.leader_id = None
        org.status = "inactive"

        result = OrganizationListItem.from_organization(org)

        assert result.code is None
        assert result.parent_id == "org-123"
        assert result.leader_id is None
        assert result.status == "inactive"


class TestOrganizationListResponse:
    """测试 OrganizationListResponse Schema"""

    def test_from_organizations_empty_list(self):
        """测试 from_organizations() 方法处理空列表"""
        from iam.schemas.organization import OrganizationListResponse

        result = OrganizationListResponse.from_organizations([])

        assert result.items == []

    def test_from_organizations_multiple_organizations(self):
        """测试 from_organizations() 方法处理多个组织"""
        from iam.schemas.organization import OrganizationListResponse

        # 创建多个 mock Organization 对象
        org1 = MagicMock()
        org1.id = "org-1"
        org1.name = "技术部"
        org1.code = "tech"
        org1.parent_id = None
        org1.sort_order = 1
        org1.leader_id = None
        org1.status = "active"

        org2 = MagicMock()
        org2.id = "org-2"
        org2.name = "产品部"
        org2.code = "product"
        org2.parent_id = None
        org2.sort_order = 2
        org2.leader_id = None
        org2.status = "active"

        result = OrganizationListResponse.from_organizations([org1, org2])

        assert len(result.items) == 2
        assert result.items[0].name == "技术部"
        assert result.items[1].name == "产品部"
