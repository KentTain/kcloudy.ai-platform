"""
TenantCacheManager 单元测试
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from framework.cache.tenant_cache_manager import (
    TenantCacheManager,
    get_cache_manager,
    init_cache_manager,
    MIN_DB,
    MAX_DB,
)
from framework.tenant.protocols import TenantCacheConfig


class TestTenantCacheManager:
    """TenantCacheManager 测试"""

    def test_manager_creation(self):
        """创建缓存管理器"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)

        assert manager._default_client is mock_client

    def test_register_tenant_db(self):
        """注册租户 Redis DB"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)

        manager.register_tenant_db("tenant-001", 3)

        assert manager._tenant_db_map["tenant-001"] == 3
        assert "tenant-001" in manager._db_usage[3]

    def test_register_tenant_db_out_of_range(self):
        """注册超出范围的 DB 编号"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)

        with pytest.raises(ValueError):
            manager.register_tenant_db("tenant-001", 20)

        with pytest.raises(ValueError):
            manager.register_tenant_db("tenant-001", -1)

    def test_unregister_tenant(self):
        """注销租户"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)
        manager.register_tenant_db("tenant-001", 3)

        manager.unregister_tenant("tenant-001")

        assert "tenant-001" not in manager._tenant_db_map

    def test_get_db_with_config(self):
        """获取 Redis DB - 有配置"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)

        config = TenantCacheConfig(db=5)
        db = manager.get_db("tenant-001", config)

        assert db == 5

    def test_get_db_from_map(self):
        """获取 Redis DB - 从注册表"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)
        manager.register_tenant_db("tenant-001", 3)

        db = manager.get_db("tenant-001")

        assert db == 3

    def test_get_db_default(self):
        """获取默认 Redis DB"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)

        db = manager.get_db(None, None)

        assert db == 0

    def test_build_key_with_config_db(self):
        """构建 Key - 有独立 Redis DB"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)
        config = TenantCacheConfig(db=3)

        key = manager._build_key("user:123", "tenant-001", config)

        assert key == "user:123"

    def test_build_key_default_db(self):
        """构建 Key - 使用默认 Redis DB"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)

        with patch("framework.cache.tenant_cache_manager.get_tenant_id", return_value="tenant-001"):
            key = manager._build_key("user:123", "tenant-001", None)

        assert key == "tenant-001:user:123"

    def test_get_stats(self):
        """获取统计信息"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)
        manager.register_tenant_db("tenant-001", 3)

        stats = manager.get_stats()

        assert stats["registered_tenants"] == 1
        assert 3 in stats["db_usage"]
        assert "total_instance_clients" in stats


class TestTenantCacheManagerPhysicalIsolation:
    """物理隔离测试"""

    def test_is_physical_isolation_with_host(self):
        """有 host 时判断为物理隔离"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)
        config = TenantCacheConfig(host="redis-tenant.example.com", port=6380)

        assert manager._is_physical_isolation(config) is True

    def test_is_physical_isolation_without_host(self):
        """无 host 时判断为非物理隔离"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)

        assert manager._is_physical_isolation(None) is False
        assert manager._is_physical_isolation(TenantCacheConfig(db=3)) is False
        assert manager._is_physical_isolation(TenantCacheConfig(host="")) is False

    def test_build_key_with_physical_isolation(self):
        """物理隔离场景不添加租户前缀"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)
        config = TenantCacheConfig(host="redis-tenant.example.com", port=6380)

        key = manager._build_key("user:123", "tenant-001", config)

        assert key == "user:123"
        assert "tenant-001" not in key

    def test_build_stream_key_with_physical_isolation(self):
        """物理隔离场景 Stream Key 不添加租户前缀"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)
        config = TenantCacheConfig(host="redis-tenant.example.com")

        stream = manager._build_stream_key("myqueue", "tenant-001", config)

        assert stream == "queue:myqueue"
        assert "tenant-001" not in stream

    @pytest.mark.asyncio
    async def test_get_client_returns_default_when_no_config(self):
        """无配置时返回默认客户端"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)

        client = await manager.get_client("tenant-001", None)

        assert client is mock_client

    @pytest.mark.asyncio
    async def test_release_idle_instances(self):
        """释放空闲实例客户端"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)

        # 模拟实例客户端
        manager._instance_clients["redis-a.com:6379"] = AsyncMock()
        manager._instance_access_times["redis-a.com:6379"] = (
            __import__("datetime").datetime.now()
        )

        # 使用超时=0确保所有客户端被释放
        released = await manager.release_idle_instances(timeout=0)

        assert released == 1
        assert "redis-a.com:6379" not in manager._instance_clients

    def test_create_instance_client(self):
        """创建实例客户端"""
        mock_client = MagicMock()
        manager = TenantCacheManager(mock_client)
        config = TenantCacheConfig(
            host="redis-t.example.com",
            port=6380,
            password="pass123",
            db=2,
        )

        client = manager._create_instance_client(config)

        assert client is not None
        pool = client.connection_pool
        assert pool.connection_kwargs["host"] == "redis-t.example.com"
        assert pool.connection_kwargs["port"] == 6380
        assert pool.connection_kwargs["password"] == "pass123"
        assert pool.connection_kwargs["db"] == 2


class TestCacheManagerGlobal:
    """全局缓存管理器测试"""

    def test_init_and_get(self):
        """初始化并获取"""
        mock_client = MagicMock()
        manager = init_cache_manager(mock_client)

        assert get_cache_manager() is manager
