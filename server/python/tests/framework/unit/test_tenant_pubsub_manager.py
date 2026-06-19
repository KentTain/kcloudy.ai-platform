"""
TenantPubSubManager 单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework.pubsub.tenant_pubsub_manager import (
    TenantPubSubManager,
    get_pubsub_manager,
    init_pubsub_manager,
)
from framework.tenant.enums import PubSubType
from framework.tenant.protocols import TenantPubSubConfig


class TestTenantPubSubManager:
    """发布订阅管理器测试"""

    def test_manager_creation(self):
        """创建发布订阅管理器"""
        mock_cache = MagicMock()
        manager = TenantPubSubManager(mock_cache)

        assert manager._cache_manager is mock_cache

    def test_is_physical_isolation_with_host(self):
        """有 host 时为物理隔离"""
        mock_cache = MagicMock()
        manager = TenantPubSubManager(mock_cache)
        config = TenantPubSubConfig(host="pubsub.example.com", port=6379)

        assert manager._is_physical_isolation(config) is True

    def test_is_physical_isolation_without_host(self):
        """无 host 时为非物理隔离"""
        mock_cache = MagicMock()
        manager = TenantPubSubManager(mock_cache)

        assert manager._is_physical_isolation(None) is False
        assert manager._is_physical_isolation(TenantPubSubConfig(host="")) is False

    def test_build_channel_name_default(self):
        """默认场景添加租户前缀"""
        mock_cache = MagicMock()
        manager = TenantPubSubManager(mock_cache)

        with patch("framework.pubsub.tenant_pubsub_manager.get_tenant_id", return_value="tenant-001"):
            name = manager._build_channel_name("events", "tenant-001", None)

        assert name == "tenant-001:channel:events"

    def test_build_channel_name_physical_isolation(self):
        """物理隔离不添加租户前缀"""
        mock_cache = MagicMock()
        manager = TenantPubSubManager(mock_cache)
        config = TenantPubSubConfig(host="pubsub.example.com", port=6379)

        name = manager._build_channel_name("events", "tenant-001", config)

        assert name == "events"
        assert "tenant-001" not in name

    def test_build_channel_name_skip_tenant(self):
        """skip_tenant 时不添加前缀"""
        mock_cache = MagicMock()
        manager = TenantPubSubManager(mock_cache)

        name = manager._build_channel_name("events", "tenant-001", None, skip_tenant=True)

        assert name == "events"

    @pytest.mark.asyncio
    async def test_publish_default(self):
        """默认频道发布消息"""
        mock_cache = MagicMock()
        mock_cache.publish = AsyncMock(return_value=3)
        manager = TenantPubSubManager(mock_cache)

        with patch("framework.pubsub.tenant_pubsub_manager.get_tenant_id", return_value="tenant-001"):
            result = await manager.publish("events", "hello", tenant_id="tenant-001")

        assert result == 3
        mock_cache.publish.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_publish_physical_isolation(self):
        """物理隔离发布消息"""
        mock_cache = MagicMock()
        mock_cache.publish = AsyncMock(return_value=1)
        manager = TenantPubSubManager(mock_cache)
        config = TenantPubSubConfig(
            type=PubSubType.REDIS,
            host="pubsub.example.com",
            port=6379,
            password="secret",
        )

        result = await manager.publish(
            "events", "hello", tenant_id="tenant-001", config=config
        )

        assert result == 1
        mock_cache.publish.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_subscribe_default(self):
        """默认订阅"""
        mock_cache = MagicMock()
        mock_client = MagicMock()
        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = AsyncMock()  # 需要 AsyncMock
        mock_client.pubsub.return_value = mock_pubsub
        mock_cache.get_client = AsyncMock(return_value=mock_client)
        manager = TenantPubSubManager(mock_cache)

        with patch("framework.pubsub.tenant_pubsub_manager.get_tenant_id", return_value="tenant-001"):
            result = await manager.subscribe("events", tenant_id="tenant-001")

        assert result is mock_pubsub
        mock_pubsub.subscribe.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_subscribe_physical_isolation(self):
        """物理隔离订阅"""
        mock_cache = MagicMock()
        mock_client = MagicMock()
        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = AsyncMock()  # 需要 AsyncMock
        mock_client.pubsub.return_value = mock_pubsub
        mock_cache.get_client = AsyncMock(return_value=mock_client)
        manager = TenantPubSubManager(mock_cache)
        config = TenantPubSubConfig(host="pubsub.example.com", port=6379)

        result = await manager.subscribe(
            "events", tenant_id="tenant-001", config=config
        )

        assert result is mock_pubsub
        mock_pubsub.subscribe.assert_awaited_once()
        # get_client 应该使用物理隔离配置调用
        mock_cache.get_client.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """取消订阅"""
        mock_cache = MagicMock()
        manager = TenantPubSubManager(mock_cache)
        mock_pubsub = MagicMock()
        mock_pubsub.unsubscribe = AsyncMock()

        await manager.unsubscribe(mock_pubsub, "events")

        mock_pubsub.unsubscribe.assert_awaited_once_with("events")


class TestPubSubManagerGlobal:
    """全局发布订阅管理器测试"""

    def test_init_and_get(self):
        mock_cache = MagicMock()
        manager = init_pubsub_manager(mock_cache)

        assert get_pubsub_manager() is manager

    def test_get_uninitialized_raises(self):
        import framework.pubsub.tenant_pubsub_manager as mod
        mod._pubsub_manager = None

        with pytest.raises(RuntimeError, match="未初始化"):
            get_pubsub_manager()
