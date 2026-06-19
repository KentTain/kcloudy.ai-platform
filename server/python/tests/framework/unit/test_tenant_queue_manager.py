"""
TenantQueueManager 单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework.queue.tenant_queue_manager import (
    TenantQueueManager,
    get_queue_manager,
    init_queue_manager,
)
from framework.tenant.enums import QueueType
from framework.tenant.protocols import TenantQueueConfig


class TestTenantQueueManager:
    """队列管理器测试"""

    def test_manager_creation(self):
        """创建队列管理器"""
        mock_cache = MagicMock()
        manager = TenantQueueManager(mock_cache)

        assert manager._cache_manager is mock_cache

    def test_is_physical_isolation_with_host(self):
        """有 host 时为物理隔离"""
        mock_cache = MagicMock()
        manager = TenantQueueManager(mock_cache)
        config = TenantQueueConfig(host="queue.example.com", port=5672)

        assert manager._is_physical_isolation(config) is True

    def test_is_physical_isolation_without_host(self):
        """无 host 时为非物理隔离"""
        mock_cache = MagicMock()
        manager = TenantQueueManager(mock_cache)

        assert manager._is_physical_isolation(None) is False
        assert manager._is_physical_isolation(TenantQueueConfig(host="")) is False

    def test_build_queue_name_default(self):
        """默认场景添加租户前缀"""
        mock_cache = MagicMock()
        manager = TenantQueueManager(mock_cache)

        with patch("framework.queue.tenant_queue_manager.get_tenant_id", return_value="tenant-001"):
            name = manager._build_queue_name("notifications", "tenant-001", None)

        assert name == "tenant-001:queue:notifications"

    def test_build_queue_name_physical_isolation(self):
        """物理隔离不添加租户前缀"""
        mock_cache = MagicMock()
        manager = TenantQueueManager(mock_cache)
        config = TenantQueueConfig(host="queue.example.com", port=5672)

        name = manager._build_queue_name("notifications", "tenant-001", config)

        assert name == "queue:notifications"
        assert "tenant-001" not in name

    def test_build_queue_name_skip_tenant(self):
        """skip_tenant 时不添加前缀"""
        mock_cache = MagicMock()
        manager = TenantQueueManager(mock_cache)

        name = manager._build_queue_name("notifications", "tenant-001", None, skip_tenant=True)

        assert name == "queue:notifications"

    @pytest.mark.asyncio
    async def test_xadd_default(self):
        """默认队列发送消息"""
        mock_cache = MagicMock()
        mock_cache.xadd = AsyncMock(return_value="msg-001")
        manager = TenantQueueManager(mock_cache)

        with patch("framework.queue.tenant_queue_manager.get_tenant_id", return_value="tenant-001"):
            result = await manager.xadd("notifications", {"text": "hello"}, tenant_id="tenant-001")

        assert result == "msg-001"
        mock_cache.xadd.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_xadd_physical_isolation(self):
        """物理隔离队列发送消息"""
        mock_cache = MagicMock()
        mock_cache.xadd = AsyncMock(return_value="msg-002")
        manager = TenantQueueManager(mock_cache)
        config = TenantQueueConfig(
            type=QueueType.RABBITMQ,
            host="queue.example.com",
            port=5672,
            password="secret",
        )

        result = await manager.xadd(
            "notifications", {"text": "hello"}, tenant_id="tenant-001", config=config
        )

        assert result == "msg-002"
        mock_cache.xadd.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_xreadgroup_physical_isolation(self):
        """物理隔离队列消费消息"""
        mock_cache = MagicMock()
        mock_cache.xreadgroup = AsyncMock(return_value=[{"msg-1": {"text": "data"}}])
        manager = TenantQueueManager(mock_cache)
        config = TenantQueueConfig(host="queue.example.com", port=5672)

        result = await manager.xreadgroup(
            "grp1", "consumer1", "notifications", tenant_id="tenant-001", config=config
        )

        assert len(result) == 1
        mock_cache.xreadgroup.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_xack_physical_isolation(self):
        """物理隔离确认消息"""
        mock_cache = MagicMock()
        mock_cache.xack = AsyncMock(return_value=1)
        manager = TenantQueueManager(mock_cache)
        config = TenantQueueConfig(host="queue.example.com", port=5672)

        result = await manager.xack(
            "notifications", "grp1", "msg-1", tenant_id="tenant-001", config=config
        )

        assert result == 1
        mock_cache.xack.assert_awaited_once()


class TestQueueManagerGlobal:
    """全局队列管理器测试"""

    def test_init_and_get(self):
        mock_cache = MagicMock()
        manager = init_queue_manager(mock_cache)

        assert get_queue_manager() is manager

    def test_get_uninitialized_raises(self):
        import framework.queue.tenant_queue_manager as mod
        mod._queue_manager = None

        with pytest.raises(RuntimeError, match="未初始化"):
            get_queue_manager()
