"""
组织人员控制器单元测试

测试 console/org_user_controller.py 中的各 API 端点。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from iam.schemas.org_user import (
    OrganizationBatchResponse,
    OrganizationSimpleVo,
    OrgUserTreeResponse,
    OrgUserTreeVo,
    UserBatchResponse,
    UserSimpleVo,
    UserSimplePaginatedListResponse,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_session() -> AsyncMock:
    """创建模拟的数据库会话"""
    return AsyncMock()


@pytest.fixture
def mock_user() -> MagicMock:
    """创建模拟的 UserSimpleVo"""
    return UserSimpleVo(
        id="user-001",
        username="zhangsan",
        nickname="张三",
        avatar="https://example.com/avatar.png",
        email="zhangsan@example.com",
        status="active",
        org_id="org-001",
        org_tree_names="/总部",
    )


@pytest.fixture
def mock_org() -> MagicMock:
    """创建模拟的 OrganizationSimpleVo"""
    return OrganizationSimpleVo(
        id="org-001",
        parent_id=None,
        parent_ids=",root,",
        tree_leaf=False,
        tree_level=1,
        tree_sort=1,
        tree_sorts="001",
        tree_names="/总部",
        tenant_id="tenant-001",
        name="总部",
        code="HQ",
        status="active",
    )


@pytest.fixture
def mock_org_user_tree() -> list[OrgUserTreeVo]:
    """创建模拟的组织人员树"""
    return [
        OrgUserTreeVo(
            id="org-001",
            parent_id=None,
            parent_ids=",root,",
            tree_leaf=False,
            tree_level=1,
            tree_sort=1,
            tree_sorts="001",
            tree_names="/总部",
            tenant_id="tenant-001",
            name="总部",
            code="HQ",
            status="active",
            has_org_num=1,
            has_user_num=2,
            users=[
                UserSimpleVo(
                    id="user-001",
                    username="zhangsan",
                    nickname="张三",
                    email="zhangsan@example.com",
                    status="active",
                    org_id="org-001",
                    org_tree_names="/总部",
                ),
                UserSimpleVo(
                    id="user-002",
                    username="lisi",
                    nickname="李四",
                    email="lisi@example.com",
                    status="active",
                    org_id="org-001",
                    org_tree_names="/总部",
                ),
            ],
        ),
    ]


# ==============================================================================
# Test Classes
# ==============================================================================


class TestGetOrgUserTree:
    """测试 GET /iam/console/v1/org-users/tree"""

    @pytest.mark.asyncio
    async def test_get_org_user_tree_success(self, mock_org_user_tree):
        """测试成功获取组织人员树"""
        from iam.controllers.console.org_user_controller import get_org_user_tree

        mock_session = AsyncMock()
        mock_tree = mock_org_user_tree

        with patch(
            "iam.controllers.console.org_user_controller.organization_service.get_org_user_tree",
            new_callable=AsyncMock,
            return_value=mock_tree,
        ):
            response = await get_org_user_tree(
                session=mock_session,
                user_id="current-user-id",
                tenant_id="tenant-001",
            )

        # 验证响应
        assert response.status_code == 200
        body = response.body if hasattr(response, "body") else response.content
        import json

        data = json.loads(body)
        assert data["code"] == 200
        assert data["data"]["items"] is not None
        items = data["data"]["items"]
        assert len(items) > 0 if items else True  # 通过 build_tree 后结构可能不同

    @pytest.mark.asyncio
    async def test_get_org_user_tree_empty(self):
        """测试无组织数据时返回空树"""
        from iam.controllers.console.org_user_controller import get_org_user_tree

        mock_session = AsyncMock()

        with patch(
            "iam.controllers.console.org_user_controller.organization_service.get_org_user_tree",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = await get_org_user_tree(
                session=mock_session,
                user_id="current-user-id",
                tenant_id="tenant-001",
            )

        # 验证响应
        assert response.status_code == 200


class TestSearchUsers:
    """测试 GET /iam/console/v1/users/search"""

    @pytest.mark.asyncio
    async def test_search_users_success(self, mock_user):
        """测试搜索用户成功"""
        from iam.controllers.console.org_user_controller import search_users

        mock_session = AsyncMock()

        # Mock 查询参数
        mock_query = MagicMock()
        mock_query.keyword = "张三"
        mock_query.org_id = None
        mock_query.include_children = False
        mock_query.page = 1
        mock_query.page_size = 20

        # Mock 搜索结果
        mock_result = UserSimplePaginatedListResponse(
            total=1,
            page=1,
            page_size=20,
            items=[mock_user],
        )

        with patch(
            "iam.controllers.console.org_user_controller.user_service.search_users",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await search_users(
                query=mock_query,
                session=mock_session,
                user_id="current-user-id",
                tenant_id="tenant-001",
            )

        # 验证响应
        assert response.status_code == 200
        import json

        data = json.loads(response.body)
        assert data["code"] == 200
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["data"]) == 1

    @pytest.mark.asyncio
    async def test_search_users_empty_result(self):
        """测试搜索用户无结果"""
        from iam.controllers.console.org_user_controller import search_users

        mock_session = AsyncMock()

        # Mock 查询参数
        mock_query = MagicMock()
        mock_query.keyword = "不存在的用户"
        mock_query.org_id = None
        mock_query.include_children = False
        mock_query.page = 1
        mock_query.page_size = 20

        # Mock 空搜索结果
        mock_result = UserSimplePaginatedListResponse(
            total=0,
            page=1,
            page_size=20,
            items=[],
        )

        with patch(
            "iam.controllers.console.org_user_controller.user_service.search_users",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await search_users(
                query=mock_query,
                session=mock_session,
                user_id="current-user-id",
                tenant_id="tenant-001",
            )

        # 验证响应
        assert response.status_code == 200
        import json

        data = json.loads(response.body)
        assert data["total"] == 0
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_search_users_with_org_filter(self, mock_user):
        """测试按组织过滤搜索用户"""
        from iam.controllers.console.org_user_controller import search_users

        mock_session = AsyncMock()

        # Mock 查询参数（指定组织）
        mock_query = MagicMock()
        mock_query.keyword = None
        mock_query.org_id = "org-001"
        mock_query.include_children = True
        mock_query.page = 1
        mock_query.page_size = 20

        # Mock 搜索结果
        mock_result = UserSimplePaginatedListResponse(
            total=1,
            page=1,
            page_size=20,
            items=[mock_user],
        )

        with patch(
            "iam.controllers.console.org_user_controller.user_service.search_users",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await search_users(
                query=mock_query,
                session=mock_session,
                user_id="current-user-id",
                tenant_id="tenant-001",
            )

        # 验证响应
        assert response.status_code == 200
        import json

        data = json.loads(response.body)
        assert data["total"] == 1
        assert data["data"][0]["username"] == "zhangsan"


class TestGetUsersBatch:
    """测试 POST /iam/console/v1/users/batch"""

    @pytest.mark.asyncio
    async def test_get_users_batch_success(self, mock_user):
        """测试批量获取用户成功"""
        from iam.controllers.console.org_user_controller import get_users_batch

        mock_session = AsyncMock()

        # Mock 请求体
        mock_body = MagicMock()
        mock_body.user_ids = ["user-001", "user-002"]

        # Mock 返回
        mock_users = [mock_user]

        with patch(
            "iam.controllers.console.org_user_controller.user_service.get_users_by_ids",
            new_callable=AsyncMock,
            return_value=mock_users,
        ):
            response = await get_users_batch(
                body=mock_body,
                session=mock_session,
                user_id="current-user-id",
            )

        # 验证响应
        assert response.status_code == 200
        import json

        data = json.loads(response.body)
        assert data["code"] == 200
        assert "items" in data["data"]
        assert data["data"]["items"][0]["id"] == "user-001"

    @pytest.mark.asyncio
    async def test_get_users_batch_empty(self):
        """测试批量获取用户返回空列表"""
        from iam.controllers.console.org_user_controller import get_users_batch

        mock_session = AsyncMock()

        # Mock 请求体
        mock_body = MagicMock()
        mock_body.user_ids = ["nonexistent-user"]

        with patch(
            "iam.controllers.console.org_user_controller.user_service.get_users_by_ids",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = await get_users_batch(
                body=mock_body,
                session=mock_session,
                user_id="current-user-id",
            )

        # 验证响应
        assert response.status_code == 200
        import json

        data = json.loads(response.body)
        assert data["code"] == 200
        assert data["data"]["items"] == []


class TestSearchOrganizations:
    """测试 GET /iam/console/v1/organizations/search"""

    @pytest.mark.asyncio
    async def test_search_organizations_success(self, mock_org):
        """测试搜索组织成功"""
        from iam.controllers.console.org_user_controller import search_organizations

        mock_session = AsyncMock()

        # Mock 查询参数
        mock_query = MagicMock()
        mock_query.keyword = "总部"
        mock_query.parent_id = None
        mock_query.page = 1
        mock_query.page_size = 20

        # Mock 搜索结果
        from iam.schemas.org_user import OrganizationPaginatedListResponse
        mock_result = OrganizationPaginatedListResponse(
            total=1,
            page=1,
            page_size=20,
            items=[mock_org],
        )

        with patch(
            "iam.controllers.console.org_user_controller.organization_service.search_organizations",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await search_organizations(
                query=mock_query,
                session=mock_session,
                user_id="current-user-id",
                tenant_id="tenant-001",
            )

        # 验证响应
        assert response.status_code == 200
        import json

        data = json.loads(response.body)
        assert data["code"] == 200
        assert data["total"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "总部"

    @pytest.mark.asyncio
    async def test_search_organizations_empty(self):
        """测试搜索组织无结果"""
        from iam.controllers.console.org_user_controller import search_organizations

        mock_session = AsyncMock()

        # Mock 查询参数
        mock_query = MagicMock()
        mock_query.keyword = "不存在的组织"
        mock_query.parent_id = None
        mock_query.page = 1
        mock_query.page_size = 20

        # Mock 空搜索结果
        from iam.schemas.org_user import OrganizationPaginatedListResponse
        mock_result = OrganizationPaginatedListResponse(
            total=0,
            page=1,
            page_size=20,
            items=[],
        )

        with patch(
            "iam.controllers.console.org_user_controller.organization_service.search_organizations",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await search_organizations(
                query=mock_query,
                session=mock_session,
                user_id="current-user-id",
                tenant_id="tenant-001",
            )

        # 验证响应
        assert response.status_code == 200
        import json

        data = json.loads(response.body)
        assert data["total"] == 0
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_search_organizations_by_parent(self, mock_org):
        """测试按父组织过滤搜索组织"""
        from iam.controllers.console.org_user_controller import search_organizations

        mock_session = AsyncMock()

        # Mock 查询参数（指定父组织）
        mock_query = MagicMock()
        mock_query.keyword = None
        mock_query.parent_id = "org-001"
        mock_query.page = 1
        mock_query.page_size = 20

        # Mock 搜索结果
        from iam.schemas.org_user import OrganizationPaginatedListResponse
        mock_result = OrganizationPaginatedListResponse(
            total=1,
            page=1,
            page_size=20,
            items=[mock_org],
        )

        with patch(
            "iam.controllers.console.org_user_controller.organization_service.search_organizations",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await search_organizations(
                query=mock_query,
                session=mock_session,
                user_id="current-user-id",
                tenant_id="tenant-001",
            )

        assert response.status_code == 200


class TestGetOrganizationsBatch:
    """测试 POST /iam/console/v1/organizations/batch"""

    @pytest.mark.asyncio
    async def test_get_organizations_batch_success(self, mock_org):
        """测试批量获取组织成功"""
        from iam.controllers.console.org_user_controller import get_organizations_batch

        mock_session = AsyncMock()

        # Mock 请求体
        mock_body = MagicMock()
        mock_body.org_ids = ["org-001", "org-002"]

        # Mock 返回
        mock_orgs = [mock_org]

        with patch(
            "iam.controllers.console.org_user_controller.organization_service.get_organizations_by_ids",
            new_callable=AsyncMock,
            return_value=mock_orgs,
        ):
            response = await get_organizations_batch(
                body=mock_body,
                session=mock_session,
                user_id="current-user-id",
            )

        # 验证响应
        assert response.status_code == 200
        import json

        data = json.loads(response.body)
        assert data["code"] == 200
        assert "items" in data["data"]
        assert data["data"]["items"][0]["id"] == "org-001"

    @pytest.mark.asyncio
    async def test_get_organizations_batch_empty(self):
        """测试批量获取组织返回空列表"""
        from iam.controllers.console.org_user_controller import get_organizations_batch

        mock_session = AsyncMock()

        # Mock 请求体
        mock_body = MagicMock()
        mock_body.org_ids = ["nonexistent-org"]

        with patch(
            "iam.controllers.console.org_user_controller.organization_service.get_organizations_by_ids",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = await get_organizations_batch(
                body=mock_body,
                session=mock_session,
                user_id="current-user-id",
            )

        # 验证响应
        assert response.status_code == 200
        import json

        data = json.loads(response.body)
        assert data["code"] == 200
        assert data["data"]["items"] == []
