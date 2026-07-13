"""
IAMTenantRoleCreator 单元测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from iam.services.tenant_role_creator import IAMTenantRoleCreator


class TestIAMTenantRoleCreator:
    """租户角色创建器测试"""

    @pytest.fixture
    def creator(self):
        """创建器实例"""
        return IAMTenantRoleCreator()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_roles_creates_all_three_roles(self, creator, mock_session):
        """测试创建三个默认角色"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        # 幂等检查：角色不存在
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        # 权限查询：空
        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = []

        # 用户角色幂等检查
        ur_result = MagicMock()
        ur_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            existing_result,  # owner 幂等检查
            existing_result,  # admin 幂等检查
            existing_result,  # member 幂等检查
            perms_result,  # 权限查询
        ]

        await creator.create_roles(mock_session, "tenant-1")

        # 应创建 3 个角色
        assert mock_session.add.call_count == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_roles_with_owner_assignment(self, creator, mock_session):
        """测试 owner 角色自动分配给创建者"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = []

        ur_result = MagicMock()
        ur_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            existing_result,  # owner
            existing_result,  # admin
            existing_result,  # member
            perms_result,  # 权限
            ur_result,  # UserRole 幂等检查
        ]

        await creator.create_roles(mock_session, "tenant-1", creator_user_id="user-1")

        # 3 角色 + 1 UserRole
        assert mock_session.add.call_count == 4

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_roles_idempotent_skip_existing(self, creator, mock_session):
        """测试幂等性：已存在角色时跳过"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        # 已存在角色
        existing_role = MagicMock()
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = existing_role

        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            existing_result,  # owner 已存在
            existing_result,  # admin 已存在
            existing_result,  # member 已存在
            perms_result,  # 权限
        ]

        await creator.create_roles(mock_session, "tenant-1")

        # 不应创建任何角色
        assert mock_session.add.call_count == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_roles_assigns_all_permissions_to_owner(
        self, creator, mock_session
    ):
        """测试 owner 获得所有权限"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        # 模拟权限
        mock_perm1 = MagicMock()
        mock_perm1.id = "perm-1"
        mock_perm2 = MagicMock()
        mock_perm2.id = "perm-2"
        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = [mock_perm1, mock_perm2]

        # RolePermission 幂等检查
        rp_result = MagicMock()
        rp_result.scalar_one_or_none.return_value = None

        ur_result = MagicMock()
        ur_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            existing_result,  # owner
            existing_result,  # admin
            existing_result,  # member
            perms_result,  # 权限列表
            rp_result,  # perm-1 幂等检查
            rp_result,  # perm-2 幂等检查
            ur_result,  # UserRole 幂等检查
        ]

        await creator.create_roles(mock_session, "tenant-1", creator_user_id="user-1")

        # 3 角色 + 2 RolePermission + 1 UserRole
        assert mock_session.add.call_count == 6

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_roles_role_permission_idempotent(self, creator, mock_session):
        """测试角色权限关联幂等性"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = [mock_perm]

        # 已存在的 RolePermission
        rp_result = MagicMock()
        rp_result.scalar_one_or_none.return_value = MagicMock()

        ur_result = MagicMock()
        ur_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            existing_result,  # owner
            existing_result,  # admin
            existing_result,  # member
            perms_result,  # 权限列表
            rp_result,  # RolePermission 幂等检查命中
            ur_result,  # UserRole 幂等检查
        ]

        await creator.create_roles(mock_session, "tenant-1", creator_user_id="user-1")

        # 3 角色 + 0 RolePermission（幂等跳过） + 1 UserRole
        assert mock_session.add.call_count == 4

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_roles_user_role_idempotent(self, creator, mock_session):
        """测试用户角色关联幂等性"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = []

        # UserRole 已存在
        ur_result = MagicMock()
        ur_result.scalar_one_or_none.return_value = MagicMock()

        mock_session.execute.side_effect = [
            existing_result,  # owner
            existing_result,  # admin
            existing_result,  # member
            perms_result,  # 权限
            ur_result,  # UserRole 幂等检查命中
        ]

        await creator.create_roles(mock_session, "tenant-1", creator_user_id="user-1")

        # 3 角色，不创建 UserRole
        assert mock_session.add.call_count == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_roles_without_creator_user(self, creator, mock_session):
        """测试不传创建者时不分配 owner 角色"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            existing_result,  # owner
            existing_result,  # admin
            existing_result,  # member
            perms_result,  # 权限
        ]

        await creator.create_roles(mock_session, "tenant-1", creator_user_id=None)

        # 只创建 3 个角色
        assert mock_session.add.call_count == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_roles_role_code_format(self, creator, mock_session):
        """测试角色编码格式"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            existing_result,
            existing_result,
            existing_result,
            perms_result,
        ]

        added_roles = []
        mock_session.add.side_effect = lambda role: added_roles.append(role)

        await creator.create_roles(mock_session, "test-tenant")

        # 验证角色编码格式
        assert added_roles[0].code == "test-tenant:owner"
        assert added_roles[1].code == "test-tenant:admin"
        assert added_roles[2].code == "test-tenant:member"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_roles_role_attributes(self, creator, mock_session):
        """测试角色属性设置"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            existing_result,
            existing_result,
            existing_result,
            perms_result,
        ]

        added_roles = []
        mock_session.add.side_effect = lambda role: added_roles.append(role)

        await creator.create_roles(mock_session, "tenant-1")

        # 验证 owner 属性
        owner = added_roles[0]
        assert owner.tenant_id == "tenant-1"
        assert owner.name == "租户所有者"
        assert owner.description == "拥有租户的所有权限"
        assert owner.is_system is False

        # 验证 admin 属性
        admin = added_roles[1]
        assert admin.name == "租户管理员"
        assert admin.description == "拥有租户的管理权限"

        # 验证 member 属性
        member = added_roles[2]
        assert member.name == "租户成员"
        assert member.description == "拥有租户的基础访问权限"
