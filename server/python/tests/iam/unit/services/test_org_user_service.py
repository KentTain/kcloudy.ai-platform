"""
组织人员树服务单元测试

测试 OrganizationService.get_org_user_tree() 和相关方法。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from iam.schemas.org_user import (
    OrgUserTreeVo,
    OrganizationSimpleVo,
    OrganizationPaginatedListResponse,
    UserSimpleVo,
    UserSimplePaginatedListResponse,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_session() -> AsyncMock:
    """创建模拟的数据库会话"""
    session = AsyncMock()
    mock_session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_organization() -> MagicMock:
    """创建模拟的 Organization 模型实例"""
    org = MagicMock()
    org.id = "org-001"
    org.parent_id = None
    org.parent_ids = ",root,"
    org.tree_leaf = False
    org.tree_level = 1
    org.tree_sort = 1
    org.tree_sorts = "001"
    org.tree_names = "/总部"
    org.tenant_id = "tenant-001"
    org.name = "总部"
    org.code = "HQ"
    org.status = "active"
    return org


@pytest.fixture
def mock_child_organization() -> MagicMock:
    """创建模拟的子组织模型实例"""
    org = MagicMock()
    org.id = "org-002"
    org.parent_id = "org-001"
    org.parent_ids = ",root,org-001,"
    org.tree_leaf = True
    org.tree_level = 2
    org.tree_sort = 1
    org.tree_sorts = "001.001"
    org.tree_names = "/总部/研发部"
    org.tenant_id = "tenant-001"
    org.name = "研发部"
    org.code = "RD"
    org.status = "active"
    return org


@pytest.fixture
def mock_user() -> MagicMock:
    """创建模拟的 User 模型实例"""
    user = MagicMock()
    user.id = "user-001"
    user.username = "zhangsan"
    user.nickname = "张三"
    user.avatar = None
    user.email = "zhangsan@example.com"
    user.status = "active"
    return user


# ==============================================================================
# Test Classes
# ==============================================================================


class TestGetOrgUserTree:
    """测试 OrganizationService.get_org_user_tree()"""

    @pytest.mark.asyncio
    async def test_get_org_user_tree_success(
        self, mock_session, mock_organization, mock_child_organization, mock_user
    ):
        """测试成功获取组织人员树"""
        # 准备测试数据
        tenant_id = "tenant-001"

        # Mock 查询组织列表
        mock_org_result = MagicMock()
        mock_org_result.scalars.return_value.all.return_value = [
            mock_organization,
            mock_child_organization,
        ]

        # Mock 查询用户-组织关联
        mock_user_row = MagicMock()
        mock_user_row.__iter__ = lambda self: iter([mock_user, "org-001", "/总部"])
        mock_user_result = MagicMock()
        mock_user_result.__iter__ = lambda self: iter([mock_user_row])

        # Mock 查询子组织数量
        mock_count_row = MagicMock()
        mock_count_row.parent_id = None
        mock_count_row.count = 1
        mock_count_result = MagicMock()
        mock_count_result.__iter__ = lambda self: iter([mock_count_row])

        # 设置 mock_session.execute 的返回值
        mock_session.execute.side_effect = [
            mock_org_result,  # 查询组织列表
            mock_user_result,  # 查询用户-组织关联
            mock_count_result,  # 查询子组织数量
        ]

        # Mock Organization.build_tree
        expected_tree = [
            OrgUserTreeVo.from_organization(mock_organization, users=[], has_org_num=1)
        ]

        with patch(
            "iam.services.organization_service.Organization.build_tree",
            return_value=expected_tree,
        ):
            from iam.services.organization_service import organization_service

            result = await organization_service.get_org_user_tree(mock_session, tenant_id)

        # 验证结果
        assert result is not None
        assert len(result) == 1
        assert result[0].id == "org-001"
        assert result[0].name == "总部"
        assert result[0].has_org_num == 1

    @pytest.mark.asyncio
    async def test_get_org_user_tree_empty_organizations(self, mock_session):
        """测试无组织时返回空列表"""
        tenant_id = "tenant-001"

        # Mock 查询组织列表为空
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session.execute.return_value = mock_result

        from iam.services.organization_service import organization_service

        result = await organization_service.get_org_user_tree(mock_session, tenant_id)

        # 验证返回空列表
        assert result == []

    @pytest.mark.asyncio
    async def test_get_org_user_tree_with_users(
        self, mock_session, mock_organization, mock_user
    ):
        """测试组织人员树包含用户列表"""
        tenant_id = "tenant-001"

        # Mock 查询组织列表
        mock_org_result = MagicMock()
        mock_org_result.scalars.return_value.all.return_value = [mock_organization]

        # Mock 查询用户-组织关联
        mock_user_row = MagicMock()
        mock_user_row.__iter__ = lambda self: iter([mock_user, "org-001", "/总部"])
        mock_user_result = MagicMock()
        mock_user_result.__iter__ = lambda self: iter([mock_user_row])

        # Mock 查询子组织数量（空）
        mock_count_result = MagicMock()
        mock_count_result.__iter__ = lambda self: iter([])

        mock_session.execute.side_effect = [
            mock_org_result,
            mock_user_result,
            mock_count_result,
        ]

        # Mock Organization.build_tree
        expected_user_vo = UserSimpleVo.from_user(mock_user, org_id="org-001", org_tree_names="/总部")
        expected_tree = [
            OrgUserTreeVo.from_organization(
                mock_organization, users=[expected_user_vo], has_org_num=0
            )
        ]

        with patch(
            "iam.services.organization_service.Organization.build_tree",
            return_value=expected_tree,
        ):
            from iam.services.organization_service import organization_service

            result = await organization_service.get_org_user_tree(mock_session, tenant_id)

        # 验证用户信息
        assert result[0].users is not None
        assert result[0].has_user_num == 1
        assert result[0].users[0].id == "user-001"
        assert result[0].users[0].username == "zhangsan"


class TestSearchOrganizations:
    """测试 OrganizationService.search_organizations()"""

    @pytest.mark.asyncio
    async def test_search_organizations_with_keyword(self, mock_session, mock_organization):
        """测试按关键词搜索组织"""
        tenant_id = "tenant-001"
        keyword = "总部"

        # Mock 查询总数
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock 查询列表
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [mock_organization]

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        from iam.services.organization_service import organization_service

        result = await organization_service.search_organizations(
            mock_session, tenant_id, keyword=keyword, page=1, page_size=20
        )

        # 验证结果
        assert isinstance(result, OrganizationPaginatedListResponse)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_search_organizations_with_parent_filter(
        self, mock_session, mock_child_organization
    ):
        """测试按父组织过滤搜索组织"""
        tenant_id = "tenant-001"
        parent_id = "org-001"

        # Mock 查询总数
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock 查询列表
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [mock_child_organization]

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        from iam.services.organization_service import organization_service

        result = await organization_service.search_organizations(
            mock_session, tenant_id, parent_id=parent_id, page=1, page_size=20
        )

        # 验证结果
        assert result.total == 1
        assert result.items[0].parent_id == parent_id

    @pytest.mark.asyncio
    async def test_search_organizations_pagination(self, mock_session, mock_organization):
        """测试组织搜索分页"""
        tenant_id = "tenant-001"

        # Mock 查询总数
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50

        # Mock 查询列表（第2页）
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [mock_organization] * 20

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        from iam.services.organization_service import organization_service

        result = await organization_service.search_organizations(
            mock_session, tenant_id, page=2, page_size=20
        )

        # 验证分页
        assert result.total == 50
        assert result.page == 2
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_search_organizations_empty_result(self, mock_session):
        """测试搜索无结果"""
        tenant_id = "tenant-001"
        keyword = "不存在的组织"

        # Mock 查询总数
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        # Mock 查询列表
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        from iam.services.organization_service import organization_service

        result = await organization_service.search_organizations(
            mock_session, tenant_id, keyword=keyword, page=1, page_size=20
        )

        # 验证空结果
        assert result.total == 0
        assert result.items == []


class TestGetOrganizationsByIds:
    """测试 OrganizationService.get_organizations_by_ids()"""

    @pytest.mark.asyncio
    async def test_get_organizations_by_ids_success(
        self, mock_session, mock_organization, mock_child_organization
    ):
        """测试批量获取组织"""
        org_ids = ["org-001", "org-002"]

        # Mock 查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            mock_organization,
            mock_child_organization,
        ]

        mock_session.execute.return_value = mock_result

        from iam.services.organization_service import organization_service

        result = await organization_service.get_organizations_by_ids(mock_session, org_ids)

        # 验证结果
        assert len(result) == 2
        assert all(isinstance(item, OrganizationSimpleVo) for item in result)
        assert result[0].id == "org-001"
        assert result[1].id == "org-002"

    @pytest.mark.asyncio
    async def test_get_organizations_by_ids_empty_list(self, mock_session):
        """测试空 ID 列表返回空列表"""
        from iam.services.organization_service import organization_service

        result = await organization_service.get_organizations_by_ids(mock_session, [])

        # 验证返回空列表
        assert result == []
        # 验证没有执行数据库查询
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_organizations_by_ids_partial_found(
        self, mock_session, mock_organization
    ):
        """测试部分 ID 找到组织"""
        org_ids = ["org-001", "nonexistent-org"]

        # Mock 查询结果（只找到一个）
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_organization]

        mock_session.execute.return_value = mock_result

        from iam.services.organization_service import organization_service

        result = await organization_service.get_organizations_by_ids(mock_session, org_ids)

        # 验证只返回找到的组织
        assert len(result) == 1
        assert result[0].id == "org-001"

    @pytest.mark.asyncio
    async def test_get_organizations_by_ids_none_found(self, mock_session):
        """测试所有 ID 都找不到"""
        org_ids = ["nonexistent-1", "nonexistent-2"]

        # Mock 查询结果为空
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session.execute.return_value = mock_result

        from iam.services.organization_service import organization_service

        result = await organization_service.get_organizations_by_ids(mock_session, org_ids)

        # 验证返回空列表
        assert result == []


class TestGetOrgUsers:
    """测试 OrganizationService.get_org_users()"""

    @pytest.mark.asyncio
    async def test_get_org_users_direct_only(self, mock_session, mock_organization, mock_user):
        """测试获取组织直属人员"""
        org_id = "org-001"

        # Mock 获取组织
        mock_session.get.return_value = mock_organization

        # Mock 查询用户列表
        mock_user_row = MagicMock()
        mock_user_row.__iter__ = lambda self: iter([mock_user, "org-001", "/总部"])
        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([mock_user_row])

        mock_session.execute.return_value = mock_result

        from iam.services.organization_service import organization_service

        result = await organization_service.get_org_users(
            mock_session, org_id, include_children=False
        )

        # 验证结果
        assert len(result) == 1
        assert isinstance(result[0], UserSimpleVo)
        assert result[0].id == "user-001"

    @pytest.mark.asyncio
    async def test_get_org_users_org_not_found(self, mock_session):
        """测试组织不存在时返回空列表"""
        org_id = "nonexistent-org"

        # Mock 组织不存在
        mock_session.get.return_value = None

        from iam.services.organization_service import organization_service

        result = await organization_service.get_org_users(
            mock_session, org_id, include_children=True
        )

        # 验证返回空列表
        assert result == []

    @pytest.mark.asyncio
    async def test_get_org_users_with_children(
        self, mock_session, mock_organization, mock_child_organization, mock_user
    ):
        """测试获取组织及下级组织人员"""
        org_id = "org-001"

        # Mock 获取组织
        mock_organization.descendant_parent_ids_prefix = MagicMock(return_value=",root,org-001,")
        mock_session.get.return_value = mock_organization

        # Mock 查询子组织 ID
        mock_org_ids_result = MagicMock()
        mock_org_ids_result.fetchall.return_value = [("org-001",), ("org-002",)]

        # Mock 查询用户列表
        mock_user_row = MagicMock()
        mock_user_row.__iter__ = lambda self: iter([mock_user, "org-001", "/总部"])
        mock_user_result = MagicMock()
        mock_user_result.__iter__ = lambda self: iter([mock_user_row])

        mock_session.execute.side_effect = [mock_org_ids_result, mock_user_result]

        from iam.services.organization_service import organization_service

        result = await organization_service.get_org_users(
            mock_session, org_id, include_children=True
        )

        # 验证结果
        assert len(result) == 1
