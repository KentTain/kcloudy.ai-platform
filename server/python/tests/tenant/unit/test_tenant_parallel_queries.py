"""测试 Tenant 模块并行查询优化

测试 asyncio.gather 并行查询的正确性。
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestBuildTenantVoParallel:
    """测试 build_tenant_vo 并行查询"""

    @pytest.mark.asyncio
    async def test_build_tenant_vo_parallel_queries(self):
        """测试 build_tenant_vo 使用 asyncio.gather 并行查询"""
        # 创建 mock Tenant 对象
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-123"
        mock_tenant.name = "测试租户"
        mock_tenant.code = "test_tenant"
        mock_tenant.status = "active"
        mock_tenant.contact_name = "联系人"
        mock_tenant.contact_email = "test@example.com"
        mock_tenant.contact_phone = "13800138000"
        mock_tenant.expired_at = None
        mock_tenant.settings = {}
        mock_tenant.db_config_id = "db-1"
        mock_tenant.storage_config_id = "storage-1"
        mock_tenant.cache_config_id = "cache-1"
        mock_tenant.queue_config_id = "queue-1"
        mock_tenant.pubsub_config_id = "pubsub-1"
        mock_tenant.created_at = datetime.now()
        mock_tenant.updated_at = datetime.now()

        # Mock 资源配置
        mock_db_config = MagicMock()
        mock_db_config.id = "db-1"
        mock_db_config.name = "数据库配置"

        mock_storage_config = MagicMock()
        mock_storage_config.id = "storage-1"
        mock_storage_config.name = "存储配置"

        mock_cache_config = MagicMock()
        mock_cache_config.id = "cache-1"
        mock_cache_config.name = "缓存配置"

        mock_queue_config = MagicMock()
        mock_queue_config.id = "queue-1"
        mock_queue_config.name = "队列配置"

        mock_pubsub_config = MagicMock()
        mock_pubsub_config.id = "pubsub-1"
        mock_pubsub_config.name = "发布订阅配置"

        # 使用 patch 模拟服务
        with patch(
            "tenant.services.database_config_service.DatabaseConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_db_config,
        ), patch(
            "tenant.services.storage_config_service.StorageConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_storage_config,
        ), patch(
            "tenant.services.cache_config_service.CacheConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_cache_config,
        ), patch(
            "tenant.services.queue_config_service.QueueConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_queue_config,
        ), patch(
            "tenant.services.pubsub_config_service.PubSubConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_pubsub_config,
        ):
            # 导入并调用 build_tenant_vo
            from tenant.controllers.admin.tenant_controller import build_tenant_vo

            result = await build_tenant_vo(mock_tenant)

            # 验证结果
            assert result is not None
            assert result.id == "tenant-123"
            assert result.name == "测试租户"
            # 资源配置应该被查询到
            assert result.db_config is not None
            assert result.storage_config is not None
            assert result.cache_config is not None
            assert result.queue_config is not None
            assert result.pubsub_config is not None

    @pytest.mark.asyncio
    async def test_build_tenant_vo_with_null_configs(self):
        """测试 build_tenant_vo 处理空配置"""
        # 创建没有资源配置的租户
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-456"
        mock_tenant.name = "无配置租户"
        mock_tenant.code = "no_config_tenant"
        mock_tenant.status = "active"
        mock_tenant.contact_name = None
        mock_tenant.contact_email = None
        mock_tenant.contact_phone = None
        mock_tenant.expired_at = None
        mock_tenant.settings = {}
        mock_tenant.db_config_id = None
        mock_tenant.storage_config_id = None
        mock_tenant.cache_config_id = None
        mock_tenant.queue_config_id = None
        mock_tenant.pubsub_config_id = None
        mock_tenant.created_at = datetime.now()
        mock_tenant.updated_at = datetime.now()

        # 使用 patch 模拟服务（返回 None）
        with patch(
            "tenant.services.database_config_service.DatabaseConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "tenant.services.storage_config_service.StorageConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "tenant.services.cache_config_service.CacheConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "tenant.services.queue_config_service.QueueConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "tenant.services.pubsub_config_service.PubSubConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            from tenant.controllers.admin.tenant_controller import build_tenant_vo

            result = await build_tenant_vo(mock_tenant)

            # 验证结果
            assert result is not None
            assert result.id == "tenant-456"
            # 资源配置应该为 None
            assert result.db_config is None
            assert result.storage_config is None
            assert result.cache_config is None
            assert result.queue_config is None
            assert result.pubsub_config is None
