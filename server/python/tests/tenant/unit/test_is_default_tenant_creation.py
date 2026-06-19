"""
租户创建时自动关联默认配置测试

测试未指定配置时自动关联默认配置、指定配置时使用指定配置。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tenant.services.tenant_service import TenantService


class TestTenantCreateAutoDefault:
    """租户创建时自动关联默认配置测试"""

    @pytest.mark.asyncio
    async def test_auto_assigns_default_database_config_when_not_specified(self, session):
        """未指定数据库配置时自动关联默认数据库配置"""
        mock_default_db = MagicMock()
        mock_default_db.id = "default-db-id"

        with patch("tenant.services.tenant_service.database_config_service") as mock_db_service, \
             patch("tenant.services.tenant_service.storage_config_service") as mock_storage_service, \
             patch("tenant.services.tenant_service.cache_config_service") as mock_cache_service, \
             patch("tenant.services.tenant_service.queue_config_service") as mock_queue_service, \
             patch("tenant.services.tenant_service.pubsub_config_service") as mock_pubsub_service, \
             patch("tenant.services.tenant_service.generate_tenant_key", return_value="test-key"), \
             patch("tenant.services.tenant_service.encrypt", return_value="encrypted-key"), \
             patch("framework.tenant.protocols.get_module_auto_assigner", return_value=None):

            session.commit = AsyncMock()
            session.refresh = AsyncMock()
            session.flush = AsyncMock()

            # 数据库配置返回默认配置，其他返回 None
            mock_db_service.get_default_config = AsyncMock(return_value=mock_default_db)
            mock_storage_service.get_default_config = AsyncMock(return_value=None)
            mock_cache_service.get_default_config = AsyncMock(return_value=None)
            mock_queue_service.get_default_config = AsyncMock(return_value=None)
            mock_pubsub_service.get_default_config = AsyncMock(return_value=None)

            await TenantService.create(
                session,
                name="测试租户",
                code="test-tenant",
            )

        mock_db_service.get_default_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_assigns_all_default_configs_when_not_specified(self, session):
        """未指定任何配置时自动关联所有默认配置"""
        mock_default_db = MagicMock()
        mock_default_db.id = "default-db-id"
        mock_default_storage = MagicMock()
        mock_default_storage.id = "default-storage-id"
        mock_default_cache = MagicMock()
        mock_default_cache.id = "default-cache-id"
        mock_default_queue = MagicMock()
        mock_default_queue.id = "default-queue-id"
        mock_default_pubsub = MagicMock()
        mock_default_pubsub.id = "default-pubsub-id"

        with patch("tenant.services.tenant_service.database_config_service") as mock_db_service, \
             patch("tenant.services.tenant_service.storage_config_service") as mock_storage_service, \
             patch("tenant.services.tenant_service.cache_config_service") as mock_cache_service, \
             patch("tenant.services.tenant_service.queue_config_service") as mock_queue_service, \
             patch("tenant.services.tenant_service.pubsub_config_service") as mock_pubsub_service, \
             patch("tenant.services.tenant_service.generate_tenant_key", return_value="test-key"), \
             patch("tenant.services.tenant_service.encrypt", return_value="encrypted-key"), \
             patch("framework.tenant.protocols.get_module_auto_assigner", return_value=None):

            session.commit = AsyncMock()
            session.refresh = AsyncMock()
            session.flush = AsyncMock()

            mock_db_service.get_default_config = AsyncMock(return_value=mock_default_db)
            mock_storage_service.get_default_config = AsyncMock(return_value=mock_default_storage)
            mock_cache_service.get_default_config = AsyncMock(return_value=mock_default_cache)
            mock_queue_service.get_default_config = AsyncMock(return_value=mock_default_queue)
            mock_pubsub_service.get_default_config = AsyncMock(return_value=mock_default_pubsub)

            await TenantService.create(
                session,
                name="测试租户",
                code="test-tenant",
            )

        # 验证所有默认配置都被查询
        mock_db_service.get_default_config.assert_called_once()
        mock_storage_service.get_default_config.assert_called_once()
        mock_cache_service.get_default_config.assert_called_once()
        mock_queue_service.get_default_config.assert_called_once()
        mock_pubsub_service.get_default_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_auto_assign_when_config_specified(self, session):
        """指定配置 ID 时不自动关联默认配置"""
        with patch("tenant.services.tenant_service.database_config_service") as mock_db_service, \
             patch("tenant.services.tenant_service.storage_config_service") as mock_storage_service, \
             patch("tenant.services.tenant_service.cache_config_service") as mock_cache_service, \
             patch("tenant.services.tenant_service.queue_config_service") as mock_queue_service, \
             patch("tenant.services.tenant_service.pubsub_config_service") as mock_pubsub_service, \
             patch("tenant.services.tenant_service.generate_tenant_key", return_value="test-key"), \
             patch("tenant.services.tenant_service.encrypt", return_value="encrypted-key"), \
             patch("framework.tenant.protocols.get_module_auto_assigner", return_value=None):

            session.commit = AsyncMock()
            session.refresh = AsyncMock()
            session.flush = AsyncMock()

            mock_db_service.get_default_config = AsyncMock(return_value=MagicMock(id="default-db"))
            mock_storage_service.get_default_config = AsyncMock(return_value=None)
            mock_cache_service.get_default_config = AsyncMock(return_value=None)
            mock_queue_service.get_default_config = AsyncMock(return_value=None)
            mock_pubsub_service.get_default_config = AsyncMock(return_value=None)

            await TenantService.create(
                session,
                name="测试租户",
                code="test-tenant",
                db_config_id="specified-db-id",
            )

        # 指定了 db_config_id，不应查询数据库默认配置
        mock_db_service.get_default_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_auto_assign_when_all_configs_specified(self, session):
        """指定所有配置 ID 时不查询任何默认配置"""
        with patch("tenant.services.tenant_service.database_config_service") as mock_db_service, \
             patch("tenant.services.tenant_service.storage_config_service") as mock_storage_service, \
             patch("tenant.services.tenant_service.cache_config_service") as mock_cache_service, \
             patch("tenant.services.tenant_service.queue_config_service") as mock_queue_service, \
             patch("tenant.services.tenant_service.pubsub_config_service") as mock_pubsub_service, \
             patch("tenant.services.tenant_service.generate_tenant_key", return_value="test-key"), \
             patch("tenant.services.tenant_service.encrypt", return_value="encrypted-key"), \
             patch("framework.tenant.protocols.get_module_auto_assigner", return_value=None):

            session.commit = AsyncMock()
            session.refresh = AsyncMock()
            session.flush = AsyncMock()

            await TenantService.create(
                session,
                name="测试租户",
                code="test-tenant",
                db_config_id="db-1",
                storage_config_id="storage-1",
                cache_config_id="cache-1",
                queue_config_id="queue-1",
                pubsub_config_id="pubsub-1",
            )

        mock_db_service.get_default_config.assert_not_called()
        mock_storage_service.get_default_config.assert_not_called()
        mock_cache_service.get_default_config.assert_not_called()
        mock_queue_service.get_default_config.assert_not_called()
        mock_pubsub_service.get_default_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_tenant_created_with_default_config_id(self, session):
        """租户创建后关联了默认配置的 ID"""
        mock_default_db = MagicMock()
        mock_default_db.id = "default-db-id"

        with patch("tenant.services.tenant_service.database_config_service") as mock_db_service, \
             patch("tenant.services.tenant_service.storage_config_service") as mock_storage_service, \
             patch("tenant.services.tenant_service.cache_config_service") as mock_cache_service, \
             patch("tenant.services.tenant_service.queue_config_service") as mock_queue_service, \
             patch("tenant.services.tenant_service.pubsub_config_service") as mock_pubsub_service, \
             patch("tenant.services.tenant_service.generate_tenant_key", return_value="test-key"), \
             patch("tenant.services.tenant_service.encrypt", return_value="encrypted-key"), \
             patch("framework.tenant.protocols.get_module_auto_assigner", return_value=None):

            session.commit = AsyncMock()
            session.refresh = AsyncMock()
            session.flush = AsyncMock()

            mock_db_service.get_default_config = AsyncMock(return_value=mock_default_db)
            mock_storage_service.get_default_config = AsyncMock(return_value=None)
            mock_cache_service.get_default_config = AsyncMock(return_value=None)
            mock_queue_service.get_default_config = AsyncMock(return_value=None)
            mock_pubsub_service.get_default_config = AsyncMock(return_value=None)

            await TenantService.create(
                session,
                name="测试租户",
                code="test-tenant",
            )

        # 验证 session.add 被调用，且创建的 Tenant 对象关联了默认配置 ID
        added_tenant = session.add.call_args[0][0]
        assert added_tenant.db_config_id == "default-db-id"

    @pytest.mark.asyncio
    async def test_tenant_created_without_default_when_none_exists(self, session):
        """没有默认配置时租户创建不关联配置"""
        with patch("tenant.services.tenant_service.database_config_service") as mock_db_service, \
             patch("tenant.services.tenant_service.storage_config_service") as mock_storage_service, \
             patch("tenant.services.tenant_service.cache_config_service") as mock_cache_service, \
             patch("tenant.services.tenant_service.queue_config_service") as mock_queue_service, \
             patch("tenant.services.tenant_service.pubsub_config_service") as mock_pubsub_service, \
             patch("tenant.services.tenant_service.generate_tenant_key", return_value="test-key"), \
             patch("tenant.services.tenant_service.encrypt", return_value="encrypted-key"), \
             patch("framework.tenant.protocols.get_module_auto_assigner", return_value=None):

            session.commit = AsyncMock()
            session.refresh = AsyncMock()
            session.flush = AsyncMock()

            # 所有默认配置查询都返回 None
            mock_db_service.get_default_config = AsyncMock(return_value=None)
            mock_storage_service.get_default_config = AsyncMock(return_value=None)
            mock_cache_service.get_default_config = AsyncMock(return_value=None)
            mock_queue_service.get_default_config = AsyncMock(return_value=None)
            mock_pubsub_service.get_default_config = AsyncMock(return_value=None)

            await TenantService.create(
                session,
                name="测试租户",
                code="test-tenant",
            )

        added_tenant = session.add.call_args[0][0]
        assert added_tenant.db_config_id is None
        assert added_tenant.storage_config_id is None
        assert added_tenant.cache_config_id is None
        assert added_tenant.queue_config_id is None
        assert added_tenant.pubsub_config_id is None
