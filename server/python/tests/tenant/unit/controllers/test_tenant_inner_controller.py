"""
Tenant Inner 控制器单元测试

测试内部接口控制器的参数校验和错误处理逻辑。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
class TestGetTenant:
    """get_tenant 控制器测试"""

    async def test_get_tenant_success(self, mock_session):
        """成功获取租户完整信息"""
        from tenant.controllers.inner.tenant_controller import get_tenant

        # Mock TenantService 返回租户
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.name = "测试租户"
        mock_tenant.code = "TEST001"
        mock_tenant.status = "active"
        mock_tenant.contact_name = None
        mock_tenant.contact_email = None
        mock_tenant.contact_phone = None
        mock_tenant.expired_at = None
        mock_tenant.database = None
        mock_tenant.storage = None
        mock_tenant.cache = None
        mock_tenant.queue = None
        mock_tenant.pubsub = None
        mock_tenant.settings = {}

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = mock_tenant

            # 执行测试
            result = await get_tenant(tenant_id="tenant-1", session=mock_session)

            # 验证返回对象
            assert result.status_code == 200
            import json

            data = json.loads(result.body.decode())
            assert data["code"] == 200
            assert data["data"]["id"] == "tenant-1"
            assert data["data"]["name"] == "测试租户"
            assert data["data"]["code"] == "TEST001"

    async def test_get_tenant_not_found(self, mock_session):
        """租户不存在时抛出 404 错误"""
        from tenant.controllers.inner.tenant_controller import get_tenant

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = None

            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await get_tenant(tenant_id="nonexistent", session=mock_session)

            assert exc_info.value.status_code == 404
            assert "租户" in exc_info.value.detail
            assert "不存在" in exc_info.value.detail


@pytest.mark.asyncio
class TestGetTenantBasic:
    """get_tenant_basic 控制器测试"""

    async def test_get_tenant_basic_success(self, mock_session):
        """成功获取租户基础信息"""
        from tenant.controllers.inner.tenant_controller import get_tenant_basic

        # Mock TenantService 返回租户
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.name = "测试租户"
        mock_tenant.code = "TEST001"
        mock_tenant.status = "active"
        mock_tenant.contact_name = None
        mock_tenant.contact_email = None
        mock_tenant.contact_phone = None
        mock_tenant.expired_at = None
        mock_tenant.db_config_id = "db-1"
        mock_tenant.storage_config_id = "storage-1"
        mock_tenant.cache_config_id = "cache-1"
        mock_tenant.queue_config_id = None
        mock_tenant.pubsub_config_id = None
        mock_tenant.encryption_key = None
        mock_tenant.settings = {}

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_resource_bindings"
        ) as mock_get:
            mock_get.return_value = mock_tenant

            # 执行测试
            result = await get_tenant_basic(tenant_id="tenant-1", session=mock_session)

            # 验证返回对象
            assert result.status_code == 200
            import json

            data = json.loads(result.body.decode())
            assert data["code"] == 200
            assert data["data"]["id"] == "tenant-1"
            assert data["data"]["name"] == "测试租户"
            assert data["data"]["db_config_id"] == "db-1"
            assert data["data"]["storage_config_id"] == "storage-1"
            assert data["data"]["cache_config_id"] == "cache-1"

    async def test_get_tenant_basic_not_found(self, mock_session):
        """租户不存在时抛出 404 错误"""
        from tenant.controllers.inner.tenant_controller import get_tenant_basic

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_resource_bindings"
        ) as mock_get:
            mock_get.return_value = None

            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await get_tenant_basic(tenant_id="nonexistent", session=mock_session)

            assert exc_info.value.status_code == 404
            assert "租户" in exc_info.value.detail
            assert "不存在" in exc_info.value.detail


@pytest.mark.asyncio
class TestGetTenantsBatch:
    """get_tenants_batch 控制器测试"""

    async def test_get_tenants_batch_success(self, mock_session):
        """成功批量获取租户"""
        from tenant.controllers.inner.tenant_controller import get_tenants_batch
        from tenant.controllers.inner.tenant_controller import BatchTenantsRequest

        # Mock TenantService 返回租户列表
        mock_tenant1 = MagicMock()
        mock_tenant1.id = "tenant-1"
        mock_tenant1.name = "租户1"
        mock_tenant1.code = "T001"
        mock_tenant1.status = "active"
        mock_tenant1.contact_name = None
        mock_tenant1.contact_email = None
        mock_tenant1.contact_phone = None
        mock_tenant1.expired_at = None
        mock_tenant1.db_config_id = "db-1"
        mock_tenant1.storage_config_id = None
        mock_tenant1.cache_config_id = None
        mock_tenant1.queue_config_id = None
        mock_tenant1.pubsub_config_id = None
        mock_tenant1.encryption_key = None
        mock_tenant1.settings = {}

        mock_tenant2 = MagicMock()
        mock_tenant2.id = "tenant-2"
        mock_tenant2.name = "租户2"
        mock_tenant2.code = "T002"
        mock_tenant2.status = "active"
        mock_tenant2.contact_name = None
        mock_tenant2.contact_email = None
        mock_tenant2.contact_phone = None
        mock_tenant2.expired_at = None
        mock_tenant2.db_config_id = "db-2"
        mock_tenant2.storage_config_id = None
        mock_tenant2.cache_config_id = None
        mock_tenant2.queue_config_id = None
        mock_tenant2.pubsub_config_id = None
        mock_tenant2.encryption_key = None
        mock_tenant2.settings = {}

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_tenants_batch"
        ) as mock_get:
            mock_get.return_value = [mock_tenant1, mock_tenant2]

            # 执行测试
            data = BatchTenantsRequest(tenant_ids=["tenant-1", "tenant-2"])
            result = await get_tenants_batch(data=data, session=mock_session)

            # 验证返回对象
            assert result.status_code == 200
            import json

            response_data = json.loads(result.body.decode())
            assert response_data["code"] == 200
            assert len(response_data["data"]) == 2
            assert response_data["data"][0]["id"] == "tenant-1"
            assert response_data["data"][1]["id"] == "tenant-2"

    async def test_get_tenants_batch_with_none(self, mock_session):
        """批量获取租户时过滤 None 值"""
        from tenant.controllers.inner.tenant_controller import get_tenants_batch
        from tenant.controllers.inner.tenant_controller import BatchTenantsRequest

        # Mock TenantService 返回包含 None 的列表
        mock_tenant1 = MagicMock()
        mock_tenant1.id = "tenant-1"
        mock_tenant1.name = "租户1"
        mock_tenant1.code = "T001"
        mock_tenant1.status = "active"
        mock_tenant1.contact_name = None
        mock_tenant1.contact_email = None
        mock_tenant1.contact_phone = None
        mock_tenant1.expired_at = None
        mock_tenant1.db_config_id = None
        mock_tenant1.storage_config_id = None
        mock_tenant1.cache_config_id = None
        mock_tenant1.queue_config_id = None
        mock_tenant1.pubsub_config_id = None
        mock_tenant1.encryption_key = None
        mock_tenant1.settings = {}

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_tenants_batch"
        ) as mock_get:
            # 返回包含 None 的列表
            mock_get.return_value = [mock_tenant1, None]

            # 执行测试
            data = BatchTenantsRequest(tenant_ids=["tenant-1", "tenant-2"])
            result = await get_tenants_batch(data=data, session=mock_session)

            # 验证返回对象：只返回存在的租户
            assert result.status_code == 200
            import json

            response_data = json.loads(result.body.decode())
            assert response_data["code"] == 200
            assert len(response_data["data"]) == 1
            assert response_data["data"][0]["id"] == "tenant-1"


@pytest.mark.asyncio
class TestGetTenantsBatchFull:
    """get_tenants_batch_full 控制器测试"""

    async def test_get_tenants_batch_full_success(self, mock_session):
        """成功批量获取租户完整信息"""
        from tenant.controllers.inner.tenant_controller import get_tenants_batch_full
        from tenant.controllers.inner.tenant_controller import BatchTenantsRequest
        from framework.tenant.context import SimpleTenant
        from tenant.models import TenantStatus

        # 准备测试数据
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.name = "租户1"
        mock_tenant.code = "T001"
        mock_tenant.status = TenantStatus.ACTIVE

        mock_simple_tenant = MagicMock(spec=SimpleTenant)
        mock_simple_tenant.id = "tenant-1"
        mock_simple_tenant.name = "租户1"
        mock_simple_tenant.code = "T001"
        mock_simple_tenant.status = TenantStatus.ACTIVE
        mock_simple_tenant.contact_name = None
        mock_simple_tenant.contact_email = None
        mock_simple_tenant.contact_phone = None
        mock_simple_tenant.expired_at = None
        mock_simple_tenant.database = None
        mock_simple_tenant.storage = None
        mock_simple_tenant.cache = None
        mock_simple_tenant.queue = None
        mock_simple_tenant.pubsub = None
        mock_simple_tenant.settings = {}

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_tenants_batch"
        ) as mock_get:
            mock_get.return_value = [mock_tenant]

            with patch(
                "tenant.controllers.inner.tenant_controller.TenantService.build_simple_tenants_batch"
            ) as mock_build:
                mock_build.return_value = [mock_simple_tenant]

                # 执行测试
                data = BatchTenantsRequest(tenant_ids=["tenant-1"])
                result = await get_tenants_batch_full(data=data, session=mock_session)

                # 验证结果
                assert result.status_code == 200
                import json

                response_data = json.loads(result.body.decode())
                assert response_data["code"] == 200
                assert len(response_data["data"]) == 1
                assert response_data["data"][0]["id"] == "tenant-1"


@pytest.mark.asyncio
class TestValidateTenantAccess:
    """validate_tenant_access 控制器测试"""

    async def test_validate_tenant_access_valid(self, mock_session):
        """用户有权访问租户"""
        from tenant.controllers.inner.tenant_controller import validate_tenant_access

        # Mock TenantService 返回租户
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.status = "active"

        # Mock IAM client 返回用户租户关联
        mock_user_tenant = MagicMock()
        mock_user_tenant.tenant_id = "tenant-1"

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = mock_tenant

            with patch("framework.clients.iam_client.get_iam_client") as mock_get_iam:
                mock_iam_client = MagicMock()
                mock_iam_client.get_user_tenants = AsyncMock(return_value=[mock_user_tenant])
                mock_get_iam.return_value = mock_iam_client

                # 执行测试
                result = await validate_tenant_access(
                    tenant_id="tenant-1", user_id="user-1", session=mock_session
                )

                # 验证返回对象
                assert result.status_code == 200
                import json

                data = json.loads(result.body.decode())
                assert data["code"] == 200
                assert data["data"]["valid"] is True
                assert data["data"]["tenant_id"] == "tenant-1"
                assert data["data"]["user_id"] == "user-1"

    async def test_validate_tenant_access_tenant_not_found(self, mock_session):
        """租户不存在时返回 valid=False"""
        from tenant.controllers.inner.tenant_controller import validate_tenant_access

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = None

            # 执行测试
            result = await validate_tenant_access(
                tenant_id="nonexistent", user_id="user-1", session=mock_session
            )

            # 验证结果
            assert result.status_code == 200
            import json

            data = json.loads(result.body.decode())
            assert data["code"] == 200
            assert data["data"]["valid"] is False
            assert data["data"]["tenant_id"] == "nonexistent"

    async def test_validate_tenant_access_tenant_inactive(self, mock_session):
        """租户已停用时返回 valid=False"""
        from tenant.controllers.inner.tenant_controller import validate_tenant_access

        # Mock TenantService 返回已停用租户
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.status = "inactive"

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = mock_tenant

            # 执行测试
            result = await validate_tenant_access(
                tenant_id="tenant-1", user_id="user-1", session=mock_session
            )

            # 验证返回对象
            assert result.status_code == 200
            import json

            data = json.loads(result.body.decode())
            assert data["code"] == 200
            assert data["data"]["valid"] is False

    async def test_validate_tenant_access_user_no_permission(self, mock_session):
        """用户无权访问租户时返回 valid=False"""
        from tenant.controllers.inner.tenant_controller import validate_tenant_access

        # Mock TenantService 返回租户
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.status = "active"

        # Mock IAM client 返回用户属于其他租户
        mock_user_tenant = MagicMock()
        mock_user_tenant.tenant_id = "tenant-2"

        with patch(
            "tenant.controllers.inner.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = mock_tenant

            with patch("framework.clients.iam_client.get_iam_client") as mock_get_iam:
                mock_iam_client = MagicMock()
                mock_iam_client.get_user_tenants = AsyncMock(return_value=[mock_user_tenant])
                mock_get_iam.return_value = mock_iam_client

                # 执行测试
                result = await validate_tenant_access(
                    tenant_id="tenant-1", user_id="user-1", session=mock_session
                )

                # 验证返回对象
                assert result.status_code == 200
                import json

                data = json.loads(result.body.decode())
                assert data["code"] == 200
                assert data["data"]["valid"] is False
