"""
Tenant 模块 TenantProvider 实现的单元测试

注意：TenantProvider 已迁移到 tenant 模块
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestTenantProvider:
    """TenantProvider 单元测试"""

    @pytest.mark.asyncio
    async def test_get_tenant_existing(self):
        """
        场景：获取存在的租户
        WHEN: 调用 get_tenant 传入存在的 tenant_id
        THEN: 返回 TenantInfo
        """
        from tenant.services.tenant_provider_impl import tenant_provider_impl

        # Mock TenantService.get_by_id
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-123"
        mock_tenant.name = "Test Tenant"
        mock_tenant.code = "test_tenant"
        mock_tenant.status = "active"
        mock_tenant.contact_name = "John"
        mock_tenant.contact_email = "john@example.com"
        mock_tenant.contact_phone = "1234567890"

        with patch(
            "tenant.services.tenant_provider_impl.TenantService.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_tenant,
        ):
            result = await tenant_provider_impl.get_tenant("tenant-123")

            assert result is not None
            assert result.id == "tenant-123"
            assert result.name == "Test Tenant"
            assert result.code == "test_tenant"
            assert result.status == "active"

    @pytest.mark.asyncio
    async def test_get_tenant_not_found(self):
        """
        场景：获取不存在的租户
        WHEN: 调用 get_tenant 传入不存在的 tenant_id
        THEN: 返回 None
        """
        from tenant.services.tenant_provider_impl import tenant_provider_impl

        with patch(
            "tenant.services.tenant_provider_impl.TenantService.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await tenant_provider_impl.get_tenant("nonexistent-id")

            assert result is None

    @pytest.mark.asyncio
    async def test_validate_access_granted(self):
        """
        场景：验证用户有权访问租户
        WHEN: 用户属于该租户
        THEN: 返回 True
        """
        from tenant.services.tenant_provider_impl import tenant_provider_impl

        # Mock IamClient.get_user_tenants
        mock_user_tenant = MagicMock()
        mock_user_tenant.tenant_id = "tenant-123"

        with patch(
            "tenant.services.tenant_provider_impl.get_iam_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_user_tenants.return_value = [mock_user_tenant]
            mock_get_client.return_value = mock_client

            result = await tenant_provider_impl.validate_access("user-123", "tenant-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_access_denied(self):
        """
        场景：验证用户无权访问租户
        WHEN: 用户不属于该租户
        THEN: 返回 False
        """
        from tenant.services.tenant_provider_impl import tenant_provider_impl

        with patch(
            "tenant.services.tenant_provider_impl.get_iam_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_user_tenants.return_value = []
            mock_get_client.return_value = mock_client

            result = await tenant_provider_impl.validate_access("user-123", "tenant-123")

            assert result is False

    @pytest.mark.asyncio
    async def test_get_user_tenants(self):
        """
        场景：获取用户所属租户列表
        WHEN: 调用 get_user_tenants
        THEN: 返回租户列表
        """
        from tenant.services.tenant_provider_impl import tenant_provider_impl

        # Mock IamClient.get_user_tenants
        mock_user_tenant1 = MagicMock()
        mock_user_tenant1.tenant_id = "tenant-1"
        mock_user_tenant2 = MagicMock()
        mock_user_tenant2.tenant_id = "tenant-2"

        # Mock TenantService.get_tenants_batch
        mock_tenant1 = MagicMock()
        mock_tenant1.id = "tenant-1"
        mock_tenant1.name = "Tenant 1"
        mock_tenant1.code = "t1"
        mock_tenant1.status = "active"
        mock_tenant1.contact_name = None
        mock_tenant1.contact_email = None
        mock_tenant1.contact_phone = None

        mock_tenant2 = MagicMock()
        mock_tenant2.id = "tenant-2"
        mock_tenant2.name = "Tenant 2"
        mock_tenant2.code = "t2"
        mock_tenant2.status = "active"
        mock_tenant2.contact_name = None
        mock_tenant2.contact_email = None
        mock_tenant2.contact_phone = None

        with patch(
            "tenant.services.tenant_provider_impl.get_iam_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_user_tenants.return_value = [mock_user_tenant1, mock_user_tenant2]
            mock_get_client.return_value = mock_client

            with patch(
                "tenant.services.tenant_provider_impl.TenantService.get_tenants_batch",
                new_callable=AsyncMock,
                return_value=[mock_tenant1, mock_tenant2],
            ):
                result = await tenant_provider_impl.get_user_tenants("user-123")

                assert len(result) == 2
                assert result[0].id == "tenant-1"
                assert result[1].id == "tenant-2"
