"""
用户搜索服务单元测试

测试 UserService.search_users() 和 get_users_by_ids() 方法。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from iam.schemas.org_user import UserSimplePaginatedListResponse, UserSimpleVo


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_session() -> AsyncMock:
    """创建模拟的数据库会话"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_user() -> MagicMock:
    """创建模拟的 User 模型实例"""
    user = MagicMock()
    user.id = "user-001"
    user.username = "zhangsan"
    user.nickname = "张三"
    user.avatar = "https://example.com/avatar.png"
    user.email = "zhangsan@example.com"
    user.status = "active"
    user.tenant_id = "tenant-001"
    user.created_at = MagicMock()
    return user


@pytest.fixture
def mock_users() -> list[MagicMock]:
    """创建多个模拟的 User 模型实例"""
    users = []
    for i in range(3):
        user = MagicMock()
        user.id = f"user-00{i + 1}"
        user.username = f"user{i + 1}"
        user.nickname = f"用户{i + 1}"
        user.avatar = None
        user.email = f"user{i + 1}@example.com"
        user.status = "active"
        user.tenant_id = "tenant-001"
        user.created_at = MagicMock()
        users.append(user)
    return users


@pytest.fixture
def mock_organization() -> MagicMock:
    """创建模拟的 Organization 模型实例"""
    org = MagicMock()
    org.id = "org-001"
    org.parent_id = None
    org.parent_ids = ",root,"
    org.tree_names = "/总部"
    org.tenant_id = "tenant-001"
    org.name = "总部"
    return org


# ==============================================================================
# Test Classes
# ==============================================================================


class TestSearchUsers:
    """测试 UserService.search_users()"""

    @pytest.mark.asyncio
    async def test_search_users_by_keyword(self, mock_session, mock_user):
        """测试按关键词搜索用户"""
        tenant_id = "tenant-001"
        keyword = "张三"

        # Mock 查询总数
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock 查询用户列表
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = [mock_user]

        # Mock 查询用户组织信息
        mock_org_row = MagicMock()
        mock_org_row.user_id = "user-001"
        mock_org_row.id = "org-001"
        mock_org_row.tree_names = "/总部"
        mock_org_result = MagicMock()
        mock_org_result.__iter__ = lambda self: iter([mock_org_row])

        mock_session.execute.side_effect = [
            mock_count_result,
            mock_user_result,
            mock_org_result,
        ]

        from iam.services.user_service import user_service

        result = await user_service.search_users(
            mock_session,
            tenant_id=tenant_id,
            keyword=keyword,
            page=1,
            page_size=20,
        )

        # 验证结果
        assert isinstance(result, UserSimplePaginatedListResponse)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].username == "zhangsan"
        assert result.items[0].nickname == "张三"

    @pytest.mark.asyncio
    async def test_search_users_by_org(self, mock_session, mock_user, mock_organization):
        """测试按组织过滤搜索用户"""
        tenant_id = "tenant-001"
        org_id = "org-001"

        # Mock 获取组织
        mock_session.get.return_value = mock_organization

        # Mock 查询组织内用户 ID
        mock_user_id_result = MagicMock()
        mock_user_id_result.all.return_value = [("user-001",)]

        # Mock 查询总数
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock 查询用户列表
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = [mock_user]

        # Mock 查询用户组织信息
        mock_org_row = MagicMock()
        mock_org_row.user_id = "user-001"
        mock_org_row.id = "org-001"
        mock_org_row.tree_names = "/总部"
        mock_org_result = MagicMock()
        mock_org_result.__iter__ = lambda self: iter([mock_org_row])

        mock_session.execute.side_effect = [
            mock_user_id_result,
            mock_count_result,
            mock_user_result,
            mock_org_result,
        ]

        from iam.services.user_service import user_service

        result = await user_service.search_users(
            mock_session,
            tenant_id=tenant_id,
            org_id=org_id,
            include_children=False,
            page=1,
            page_size=20,
        )

        # 验证结果
        assert result.total == 1
        assert result.items[0].org_id == "org-001"

    @pytest.mark.asyncio
    async def test_search_users_by_org_with_children(
        self, mock_session, mock_user, mock_organization
    ):
        """测试按组织过滤搜索用户（包含下级）"""
        tenant_id = "tenant-001"
        org_id = "org-001"

        # Mock 组织支持子组织查询
        mock_organization.descendant_parent_ids_prefix = MagicMock(
            return_value=",root,org-001,"
        )

        # Mock 获取组织
        mock_session.get.return_value = mock_organization

        # Mock 查询子组织 ID
        mock_org_ids_result = MagicMock()
        mock_org_ids_result.all.return_value = [("org-001",), ("org-002",)]

        # Mock 查询组织内用户 ID
        mock_user_id_result = MagicMock()
        mock_user_id_result.all.return_value = [("user-001",)]

        # Mock 查询总数
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock 查询用户列表
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = [mock_user]

        # Mock 查询用户组织信息
        mock_org_row = MagicMock()
        mock_org_row.user_id = "user-001"
        mock_org_row.id = "org-001"
        mock_org_row.tree_names = "/总部"
        mock_org_result = MagicMock()
        mock_org_result.__iter__ = lambda self: iter([mock_org_row])

        mock_session.execute.side_effect = [
            mock_org_ids_result,
            mock_user_id_result,
            mock_count_result,
            mock_user_result,
            mock_org_result,
        ]

        from iam.services.user_service import user_service

        result = await user_service.search_users(
            mock_session,
            tenant_id=tenant_id,
            org_id=org_id,
            include_children=True,
            page=1,
            page_size=20,
        )

        # 验证结果
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_search_users_pagination(self, mock_session, mock_users):
        """测试用户搜索分页"""
        tenant_id = "tenant-001"

        # Mock 查询总数
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 30

        # Mock 查询用户列表
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = mock_users

        # Mock 查询用户组织信息（空）
        mock_org_result = MagicMock()
        mock_org_result.__iter__ = lambda self: iter([])

        mock_session.execute.side_effect = [
            mock_count_result,
            mock_user_result,
            mock_org_result,
        ]

        from iam.services.user_service import user_service

        result = await user_service.search_users(
            mock_session,
            tenant_id=tenant_id,
            page=2,
            page_size=3,
        )

        # 验证分页
        assert result.total == 30
        assert result.page == 2
        assert result.page_size == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_search_users_empty_result(self, mock_session):
        """测试搜索无结果"""
        tenant_id = "tenant-001"
        keyword = "不存在的用户"

        # Mock 查询总数
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        # Mock 查询用户列表
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_user_result]

        from iam.services.user_service import user_service

        result = await user_service.search_users(
            mock_session,
            tenant_id=tenant_id,
            keyword=keyword,
            page=1,
            page_size=20,
        )

        # 验证空结果
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_search_users_org_not_found(self, mock_session, mock_user):
        """测试组织不存在时返回空列表"""
        tenant_id = "tenant-001"
        org_id = "nonexistent-org"

        # Mock 组织不存在
        mock_session.get.return_value = None

        # Mock 查询总数（组织不存在时，代码会使用 [org_id] 作为 org_ids 继续查询）
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        # Mock 查询用户列表
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = []

        # Mock 查询组织内用户 ID（空结果）
        mock_user_id_result = MagicMock()
        mock_user_id_result.all.return_value = []

        mock_session.execute.side_effect = [
            mock_user_id_result,
            mock_count_result,
            mock_user_result,
        ]

        from iam.services.user_service import user_service

        result = await user_service.search_users(
            mock_session,
            tenant_id=tenant_id,
            org_id=org_id,
            include_children=True,
            page=1,
            page_size=20,
        )

        # 验证结果（组织不存在时，查询结果为空）
        assert result.total == 0
        assert result.items == []


class TestGetUsersByIds:
    """测试 UserService.get_users_by_ids()"""

    @pytest.mark.asyncio
    async def test_get_users_by_ids_success(self, mock_session, mock_user):
        """测试批量获取用户成功"""
        user_ids = ["user-001"]

        # Mock 查询用户列表
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = [mock_user]

        # Mock 查询用户组织信息
        mock_org_row = MagicMock()
        mock_org_row.user_id = "user-001"
        mock_org_row.id = "org-001"
        mock_org_row.tree_names = "/总部"
        mock_org_result = MagicMock()
        mock_org_result.__iter__ = lambda self: iter([mock_org_row])

        mock_session.execute.side_effect = [mock_user_result, mock_org_result]

        from iam.services.user_service import user_service

        result = await user_service.get_users_by_ids(mock_session, user_ids)

        # 验证结果
        assert len(result) == 1
        assert isinstance(result[0], UserSimpleVo)
        assert result[0].id == "user-001"
        assert result[0].username == "zhangsan"
        assert result[0].org_id == "org-001"

    @pytest.mark.asyncio
    async def test_get_users_by_ids_empty_list(self, mock_session):
        """测试空 ID 列表返回空列表"""
        from iam.services.user_service import user_service

        result = await user_service.get_users_by_ids(mock_session, [])

        # 验证返回空列表
        assert result == []
        # 验证没有执行数据库查询
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_users_by_ids_multiple_users(self, mock_session, mock_users):
        """测试批量获取多个用户"""
        user_ids = ["user-001", "user-002", "user-003"]

        # Mock 查询用户列表
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = mock_users

        # Mock 查询用户组织信息
        mock_org_rows = []
        for user in mock_users:
            row = MagicMock()
            row.user_id = user.id
            row.id = "org-001"
            row.tree_names = "/总部"
            mock_org_rows.append(row)

        mock_org_result = MagicMock()
        mock_org_result.__iter__ = lambda self: iter(mock_org_rows)

        mock_session.execute.side_effect = [mock_user_result, mock_org_result]

        from iam.services.user_service import user_service

        result = await user_service.get_users_by_ids(mock_session, user_ids)

        # 验证结果
        assert len(result) == 3
        assert all(isinstance(item, UserSimpleVo) for item in result)

    @pytest.mark.asyncio
    async def test_get_users_by_ids_partial_found(self, mock_session, mock_user):
        """测试部分用户 ID 找到用户"""
        user_ids = ["user-001", "nonexistent-user"]

        # Mock 查询用户列表（只找到一个）
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = [mock_user]

        # Mock 查询用户组织信息
        mock_org_row = MagicMock()
        mock_org_row.user_id = "user-001"
        mock_org_row.id = "org-001"
        mock_org_row.tree_names = "/总部"
        mock_org_result = MagicMock()
        mock_org_result.__iter__ = lambda self: iter([mock_org_row])

        mock_session.execute.side_effect = [mock_user_result, mock_org_result]

        from iam.services.user_service import user_service

        result = await user_service.get_users_by_ids(mock_session, user_ids)

        # 验证只返回找到的用户
        assert len(result) == 1
        assert result[0].id == "user-001"

    @pytest.mark.asyncio
    async def test_get_users_by_ids_none_found(self, mock_session):
        """测试所有用户 ID 都找不到"""
        user_ids = ["nonexistent-1", "nonexistent-2"]

        # Mock 查询用户列表为空
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = []

        mock_session.execute.return_value = mock_user_result

        from iam.services.user_service import user_service

        result = await user_service.get_users_by_ids(mock_session, user_ids)

        # 验证返回空列表
        assert result == []

    @pytest.mark.asyncio
    async def test_get_users_by_ids_without_org(self, mock_session, mock_user):
        """测试用户无组织关联时的处理"""
        user_ids = ["user-001"]

        # Mock 查询用户列表
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = [mock_user]

        # Mock 查询用户组织信息（无组织）
        mock_org_result = MagicMock()
        mock_org_result.__iter__ = lambda self: iter([])

        mock_session.execute.side_effect = [mock_user_result, mock_org_result]

        from iam.services.user_service import user_service

        result = await user_service.get_users_by_ids(mock_session, user_ids)

        # 验证结果（用户存在但无组织信息）
        assert len(result) == 1
        assert result[0].id == "user-001"
        assert result[0].org_id is None
        assert result[0].org_tree_names is None
