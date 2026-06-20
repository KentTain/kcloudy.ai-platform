"""
Tenant 模块 TenantProvider 实现的单元测试

注意：TenantProvider 已迁移到 tenant 模块
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestTenantProvider:
    """TenantProvider 单元测试"""

    @pytest.mark.asyncio
    async def test_get_tenant_existing(self):
        """
        场景：获取存在的租户
        WHEN: 调用 get_tenant 传入存在的 tenant_id
        THEN: 返回 TenantInfo
        """
        from framework.tenant.context import SimpleTenant

        # 创建预期的 SimpleTenant
        expected_tenant = SimpleTenant(
            id="tenant-123",
            name="Test Tenant",
            code="test_tenant",
            status="active",
        )

        # Mock TenantCache.get 返回 None（缓存未命中）
        # Mock get_task_session 返回 mock session
        # Mock TenantService.get_by_id 返回 SimpleTenant
        with patch("framework.tenant.cache.TenantCache.get", new_callable=AsyncMock, return_value=None):
            with patch("framework.database.dependencies.get_task_session") as mock_session_ctx:
                mock_session = AsyncMock()
                mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

                with patch(
                    "tenant.services.tenant_provider_impl.TenantService.get_by_id",
                    new_callable=AsyncMock,
                    return_value=expected_tenant,
                ):
                    with patch("framework.tenant.cache.TenantCache.set", new_callable=AsyncMock):
                        from tenant.services.tenant_provider_impl import tenant_provider_impl
                        result = await tenant_provider_impl.get_tenant("tenant-123")

                        assert result is not None
                        assert result.id == "tenant-123"
                        assert result.name == "Test Tenant"
                        assert result.code == "test_tenant"

    @pytest.mark.asyncio
    async def test_get_tenant_not_found(self):
        """
        场景：获取不存在的租户
        WHEN: 调用 get_tenant 传入不存在的 tenant_id
        THEN: 返回 None
        """
        # Mock TenantCache.get 返回 None（缓存未命中）
        with patch("framework.tenant.cache.TenantCache.get", new_callable=AsyncMock, return_value=None):
            with patch("framework.database.dependencies.get_task_session") as mock_session_ctx:
                mock_session = AsyncMock()
                mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

                with patch(
                    "tenant.services.tenant_provider_impl.TenantService.get_by_id",
                    new_callable=AsyncMock,
                    return_value=None,
                ):
                    from tenant.services.tenant_provider_impl import tenant_provider_impl
                    result = await tenant_provider_impl.get_tenant("nonexistent-id")

                    assert result is None

    @pytest.mark.asyncio
    async def test_validate_access_granted(self):
        """
        场景：验证用户有权访问租户
        WHEN: 用户属于该租户
        THEN: 返回 True
        """
        # Mock IamClient.get_user_tenants
        mock_user_tenant = MagicMock()
        mock_user_tenant.tenant_id = "tenant-123"

        with patch(
            "framework.clients.iam_client.get_iam_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_user_tenants.return_value = [mock_user_tenant]
            mock_get_client.return_value = mock_client

            from tenant.services.tenant_provider_impl import tenant_provider_impl
            result = await tenant_provider_impl.validate_access("user-123", "tenant-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_access_denied(self):
        """
        场景：验证用户无权访问租户
        WHEN: 用户不属于该租户
        THEN: 返回 False
        """
        with patch(
            "framework.clients.iam_client.get_iam_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_user_tenants.return_value = []
            mock_get_client.return_value = mock_client

            from tenant.services.tenant_provider_impl import tenant_provider_impl
            result = await tenant_provider_impl.validate_access("user-123", "tenant-123")

            assert result is False

    @pytest.mark.asyncio
    async def test_get_user_tenants(self):
        """
        场景：获取用户所属租户列表
        WHEN: 调用 get_user_tenants
        THEN: 返回租户列表
        """
        from framework.tenant.context import SimpleTenant

        # 创建预期的 SimpleTenant 列表
        expected_tenants = [
            SimpleTenant(id="tenant-1", name="Tenant 1", code="t1", status="active"),
            SimpleTenant(id="tenant-2", name="Tenant 2", code="t2", status="active"),
        ]

        # Mock IamClient.get_user_tenants 返回用户-租户关联
        mock_user_tenant1 = MagicMock()
        mock_user_tenant1.tenant_id = "tenant-1"
        mock_user_tenant2 = MagicMock()
        mock_user_tenant2.tenant_id = "tenant-2"

        # Mock Tenant ORM 对象
        mock_tenant1 = MagicMock()
        mock_tenant1.id = "tenant-1"
        mock_tenant1.name = "Tenant 1"
        mock_tenant1.code = "t1"
        mock_tenant1.status = "active"
        mock_tenant1.db_config_id = None
        mock_tenant1.storage_config_id = None
        mock_tenant1.cache_config_id = None

        mock_tenant2 = MagicMock()
        mock_tenant2.id = "tenant-2"
        mock_tenant2.name = "Tenant 2"
        mock_tenant2.code = "t2"
        mock_tenant2.status = "active"
        mock_tenant2.db_config_id = None
        mock_tenant2.storage_config_id = None
        mock_tenant2.cache_config_id = None

        with patch(
            "framework.clients.iam_client.get_iam_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_user_tenants.return_value = [mock_user_tenant1, mock_user_tenant2]
            mock_get_client.return_value = mock_client

            with patch("framework.database.dependencies.get_task_session") as mock_session_ctx:
                mock_session = AsyncMock()
                mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

                with patch(
                    "tenant.services.tenant_provider_impl.TenantService.get_tenants_batch",
                    new_callable=AsyncMock,
                    return_value=[mock_tenant1, mock_tenant2],
                ):
                    # 直接 mock build_simple_tenants_batch 返回预期结果
                    with patch(
                        "tenant.services.tenant_provider_impl.TenantService.build_simple_tenants_batch",
                        new_callable=AsyncMock,
                        return_value=expected_tenants,
                    ):
                        from tenant.services.tenant_provider_impl import (
                            tenant_provider_impl,
                        )
                        result = await tenant_provider_impl.get_user_tenants("user-123")

                        assert len(result) == 2
                        assert result[0].id == "tenant-1"
                        assert result[1].id == "tenant-2"
