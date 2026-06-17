"""
IamClient 单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from framework.clients.iam_client import IamClient, UserTenantInfo


class TestIamClientGetUserTenants:
    """get_user_tenants 方法测试"""

    @pytest.mark.asyncio
    async def test_monolith_mode_returns_user_tenants(self):
        """单体模式返回用户租户列表"""
        client = IamClient(inner_url=None)  # 单体模式

        mock_user_tenant_1 = MagicMock()
        mock_user_tenant_1.tenant_id = "tenant-1"
        mock_user_tenant_1.role = "admin"
        mock_user_tenant_1.is_default = True

        mock_user_tenant_2 = MagicMock()
        mock_user_tenant_2.tenant_id = "tenant-2"
        mock_user_tenant_2.role = "member"
        mock_user_tenant_2.is_default = False

        with patch("framework.database.core.engine.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [
                mock_user_tenant_1,
                mock_user_tenant_2,
            ]
            mock_session_context.execute.return_value = mock_result

            result = await client.get_user_tenants("user-1")

        assert len(result) == 2
        assert result[0].tenant_id == "tenant-1"
        assert result[0].role == "admin"
        assert result[0].is_default is True
        assert result[1].tenant_id == "tenant-2"
        assert result[1].role == "member"
        assert result[1].is_default is False

    @pytest.mark.asyncio
    async def test_monolith_mode_returns_empty_list(self):
        """单体模式用户无租户时返回空列表"""
        client = IamClient(inner_url=None)

        with patch("framework.database.core.engine.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session_context.execute.return_value = mock_result

            result = await client.get_user_tenants("user-no-tenants")

        assert result == []


class TestIamClientGetTenantUserIds:
    """get_tenant_user_ids 方法测试"""

    @pytest.mark.asyncio
    async def test_monolith_mode_returns_user_ids(self):
        """单体模式返回租户用户 ID 列表"""
        client = IamClient(inner_url=None)

        with patch("framework.database.core.engine.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.all.return_value = [("user-1",), ("user-2",)]
            mock_session_context.execute.return_value = mock_result

            result = await client.get_tenant_user_ids("tenant-1")

        assert result == ["user-1", "user-2"]

    @pytest.mark.asyncio
    async def test_monolith_mode_returns_empty_list(self):
        """单体模式租户无用户时返回空列表"""
        client = IamClient(inner_url=None)

        with patch("framework.database.core.engine.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_session_context.execute.return_value = mock_result

            result = await client.get_tenant_user_ids("tenant-no-users")

        assert result == []


class TestIamClientGetUserTenantsMicroservice:
    """get_user_tenants 微服务模式测试"""

    @pytest.mark.asyncio
    async def test_microservice_mode_returns_user_tenants(self):
        """微服务模式调用 inner 接口返回用户租户列表"""
        client = IamClient(inner_url="http://iam-service:8000")

        # Mock HTTP 响应
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(
            return_value={
                "user_id": "user-1",
                "tenants": [
                    {"tenant_id": "tenant-1", "role": "admin", "is_default": True},
                    {"tenant_id": "tenant-2", "role": "member", "is_default": False},
                ],
            }
        )
        client._http_client = mock_http_client

        result = await client.get_user_tenants("user-1")

        assert len(result) == 2
        assert result[0].tenant_id == "tenant-1"
        assert result[0].role == "admin"
        assert result[0].is_default is True

        # 验证调用了正确的接口
        mock_http_client.get.assert_called_once_with("/iam/inner/v1/users/user-1/tenants")

    @pytest.mark.asyncio
    async def test_microservice_mode_returns_empty_list(self):
        """微服务模式返回空列表"""
        client = IamClient(inner_url="http://iam-service:8000")

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value={"user_id": "user-1", "tenants": []})
        client._http_client = mock_http_client

        result = await client.get_user_tenants("user-1")

        assert result == []


class TestIamClientGetTenantUserIdsMicroservice:
    """get_tenant_user_ids 微服务模式测试"""

    @pytest.mark.asyncio
    async def test_microservice_mode_returns_user_ids(self):
        """微服务模式调用 inner 接口返回用户 ID 列表"""
        client = IamClient(inner_url="http://iam-service:8000")

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(
            return_value={"tenant_id": "tenant-1", "user_ids": ["user-1", "user-2"]}
        )
        client._http_client = mock_http_client

        result = await client.get_tenant_user_ids("tenant-1")

        assert result == ["user-1", "user-2"]
        mock_http_client.get.assert_called_once_with("/iam/inner/v1/tenants/tenant-1/users")

    @pytest.mark.asyncio
    async def test_microservice_mode_returns_empty_list(self):
        """微服务模式返回空列表"""
        client = IamClient(inner_url="http://iam-service:8000")

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value={"tenant_id": "tenant-1", "user_ids": []})
        client._http_client = mock_http_client

        result = await client.get_tenant_user_ids("tenant-1")

        assert result == []
