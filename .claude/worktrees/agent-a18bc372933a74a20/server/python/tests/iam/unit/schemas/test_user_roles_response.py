"""测试 IAM 模块 Schema 转换方法

测试 UserRoleItem、UserRolesResponse、DepartmentListItem、DepartmentListResponse 转换方法。
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest


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


class TestDepartmentListItem:
    """测试 DepartmentListItem Schema"""

    def test_from_department_basic_fields(self):
        """测试 from_department() 方法基础字段映射"""
        from iam.schemas.department import DepartmentListItem

        # 创建 mock Department 对象
        dept = MagicMock()
        dept.id = "dept-123"
        dept.name = "技术部"
        dept.code = "tech"
        dept.parent_id = None
        dept.sort_order = 1
        dept.leader_id = "user-456"
        dept.status = "active"

        result = DepartmentListItem.from_department(dept)

        assert result.id == "dept-123"
        assert result.name == "技术部"
        assert result.code == "tech"
        assert result.parent_id is None
        assert result.sort_order == 1
        assert result.leader_id == "user-456"
        assert result.status == "active"

    def test_from_department_null_fields(self):
        """测试 from_department() 方法处理空字段"""
        from iam.schemas.department import DepartmentListItem

        dept = MagicMock()
        dept.id = "dept-456"
        dept.name = "新部门"
        dept.code = None
        dept.parent_id = "dept-123"
        dept.sort_order = 0
        dept.leader_id = None
        dept.status = "inactive"

        result = DepartmentListItem.from_department(dept)

        assert result.code is None
        assert result.parent_id == "dept-123"
        assert result.leader_id is None
        assert result.status == "inactive"


class TestDepartmentListResponse:
    """测试 DepartmentListResponse Schema"""

    def test_from_departments_empty_list(self):
        """测试 from_departments() 方法处理空列表"""
        from iam.schemas.department import DepartmentListResponse

        result = DepartmentListResponse.from_departments([])

        assert result.items == []

    def test_from_departments_multiple_departments(self):
        """测试 from_departments() 方法处理多个部门"""
        from iam.schemas.department import DepartmentListResponse

        # 创建多个 mock Department 对象
        dept1 = MagicMock()
        dept1.id = "dept-1"
        dept1.name = "技术部"
        dept1.code = "tech"
        dept1.parent_id = None
        dept1.sort_order = 1
        dept1.leader_id = None
        dept1.status = "active"

        dept2 = MagicMock()
        dept2.id = "dept-2"
        dept2.name = "产品部"
        dept2.code = "product"
        dept2.parent_id = None
        dept2.sort_order = 2
        dept2.leader_id = None
        dept2.status = "active"

        result = DepartmentListResponse.from_departments([dept1, dept2])

        assert len(result.items) == 2
        assert result.items[0].name == "技术部"
        assert result.items[1].name == "产品部"
