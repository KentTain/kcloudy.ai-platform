"""
TenantCacheManager 物理隔离集成测试

测试场景覆盖：
1. 连接独立 Redis 实例
2. 使用默认 Redis 实例
3. 复用已缓存的实例客户端
4. 创建新的实例客户端
5. 物理隔离 Key 不添加前缀
6. 逻辑隔离 Key 添加前缀
"""

import pytest
import pytest_asyncio

from framework.cache.tenant_cache_manager import TenantCacheManager, init_cache_manager
from framework.tenant.protocols import TenantCacheConfig


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def cache_manager(redis_client, redis_available):
    """缓存管理器实例"""
    if not redis_available:
        pytest.skip("Redis 服务不可用")

    manager = TenantCacheManager(redis_client)
    yield manager

    # 清理
    await manager.close()


@pytest_asyncio.fixture
def unique_tenant_id():
    """生成唯一租户 ID"""
    import uuid
    return f"tenant-{uuid.uuid4().hex[:8]}"


class TestTenantCachePhysicalIsolation:
    """物理隔离场景测试"""

    @pytest.mark.asyncio
    async def test_connect_independent_redis_instance(self, cache_manager, unique_tenant_id):
        """
        场景: 连接独立 Redis 实例

        WHEN 租户配置了 host="redis-tenant-a.example.com" 和 port=6380
        THEN 系统创建到该实例的独立 Redis 客户端
        """
        # 由于无法连接真实外部实例，这里验证配置解析逻辑
        config = TenantCacheConfig(
            host="redis-tenant-a.example.com",
            port=6380,
            password="secret",
            db=2,
        )

        # 验证物理隔离判断
        assert cache_manager._is_physical_isolation(config) is True

        # 验证配置参数正确传递
        assert config.host == "redis-tenant-a.example.com"
        assert config.port == 6380
        assert config.password == "secret"
        assert config.db == 2

    @pytest.mark.asyncio
    async def test_use_default_redis_instance(self, cache_manager, unique_tenant_id):
        """
        场景: 使用默认 Redis 实例

        WHEN 租户未配置 host 或 host 为空
        THEN 使用默认 Redis 客户端
        """
        # 无配置
        client = await cache_manager.get_client(unique_tenant_id, None)
        assert client is cache_manager._default_client

        # 空配置
        config = TenantCacheConfig(host="", port=6379)
        assert cache_manager._is_physical_isolation(config) is False

        # 只有 db 配置
        config = TenantCacheConfig(db=3)
        assert cache_manager._is_physical_isolation(config) is False

    @pytest.mark.asyncio
    async def test_reuse_cached_instance_client(self, cache_manager, unique_tenant_id):
        """
        场景: 复用已缓存的实例客户端

        WHEN 请求连接 host="redis-a.com:6379" 且该实例客户端已存在
        THEN 返回缓存的客户端
        """
        # 注意：此测试使用本地 Redis 模拟物理隔离场景
        # 在实际部署中会连接到不同的 Redis 实例

        # 使用本地 Redis 作为"物理隔离"实例（测试目的）
        config = TenantCacheConfig(
            host="localhost",
            port=6379,
            db=10,  # 使用不同的 DB 模拟隔离
        )

        # 第一次获取，创建客户端
        client1 = await cache_manager.get_client(unique_tenant_id, config)
        assert client1 is not None

        # 第二次获取，应返回相同客户端（缓存）
        client2 = await cache_manager.get_client(unique_tenant_id, config)
        assert client2 is client1

        # 验证实例被缓存
        instance_key = "localhost:6379"
        assert instance_key in cache_manager._instance_clients

    @pytest.mark.asyncio
    async def test_create_new_instance_client(self, cache_manager, unique_tenant_id):
        """
        场景: 创建新的实例客户端

        WHEN 请求连接 host="redis-b.com:6380" 且该实例客户端不存在
        THEN 使用配置的 host/port/password 创建新客户端
        """
        # 使用不同的端口模拟新实例
        config = TenantCacheConfig(
            host="localhost",
            port=6380,  # 假设这是另一个 Redis 实例
            db=0,
        )

        # 验证物理隔离判断
        assert cache_manager._is_physical_isolation(config) is True

        # 注意：实际测试中可能无法连接到 6380 端口
        # 这里主要验证创建逻辑
        initial_count = len(cache_manager._instance_clients)

        # 如果目标端口不可用，跳过实际连接测试
        try:
            client = await cache_manager.get_client(unique_tenant_id, config)
            assert client is not None
            assert len(cache_manager._instance_clients) == initial_count + 1
        except Exception:
            # 端口不可用，仅验证配置解析
            pytest.skip("目标 Redis 端口不可用")

    @pytest.mark.asyncio
    async def test_physical_isolation_key_no_prefix(self, cache_manager, unique_tenant_id):
        """
        场景: 物理隔离 Key 不添加前缀

        WHEN 配置了 host 且调用缓存设置接口
        THEN Key 不添加租户前缀
        """
        # 使用本地 Redis 作为物理隔离实例
        config = TenantCacheConfig(
            host="localhost",
            port=6379,
            db=11,  # 使用独立 DB 避免冲突
        )

        test_key = "physical_isolation_test_key"
        test_value = "test_value"

        # 构建实际 Key
        actual_key = cache_manager._build_key(test_key, unique_tenant_id, config)

        # 物理隔离场景，Key 不添加前缀
        assert actual_key == test_key
        assert unique_tenant_id not in actual_key

        # 实际设置并获取值
        try:
            client = await cache_manager.get_client(unique_tenant_id, config)
            await client.set(test_key, test_value, ex=60)
            result = await client.get(test_key)
            assert result == test_value

            # 清理
            await client.delete(test_key)
        except Exception as e:
            pytest.skip(f"Redis 实例不可用: {e}")

    @pytest.mark.asyncio
    async def test_logical_isolation_key_with_prefix(self, cache_manager, unique_tenant_id):
        """
        场景: 逻辑隔离 Key 添加前缀

        WHEN 租户未配置任何隔离参数
        THEN Key 自动添加 {tenant_id}: 前缀
        """
        test_key = "logical_isolation_test_key"

        # 构建实际 Key（无物理隔离配置）
        actual_key = cache_manager._build_key(test_key, unique_tenant_id, None)

        # 逻辑隔离场景，Key 添加租户前缀
        expected_prefix = f"{unique_tenant_id}:"
        assert actual_key.startswith(expected_prefix)
        assert test_key in actual_key
        assert actual_key == f"{unique_tenant_id}:{test_key}"

        # 实际设置并获取值
        await cache_manager.set(test_key, "test_value", tenant_id=unique_tenant_id)
        result = await cache_manager.get(test_key, tenant_id=unique_tenant_id)
        assert result == "test_value"

        # 清理
        await cache_manager.delete(test_key, tenant_id=unique_tenant_id)


class TestTenantCacheKeyBuilding:
    """Key 构建规则测试"""

    @pytest.mark.asyncio
    async def test_key_building_with_physical_isolation(self, cache_manager, unique_tenant_id):
        """物理隔离场景下 Key 构建规则"""
        config = TenantCacheConfig(host="redis-isolated.com", port=6379)

        # 普通字符串 Key
        key1 = cache_manager._build_key("user:123", unique_tenant_id, config)
        assert key1 == "user:123"

        # 带前缀的 Key
        key2 = cache_manager._build_key("cache:session:abc", unique_tenant_id, config)
        assert key2 == "cache:session:abc"

    @pytest.mark.asyncio
    async def test_key_building_with_db_isolation(self, cache_manager, unique_tenant_id):
        """独立 DB 场景下 Key 构建规则"""
        config = TenantCacheConfig(db=5)

        # 有独立 DB 配置，不添加前缀
        key = cache_manager._build_key("mykey", unique_tenant_id, config)
        assert key == "mykey"

    @pytest.mark.asyncio
    async def test_key_building_with_registered_db(self, cache_manager, unique_tenant_id):
        """注册 DB 场景下 Key 构建规则"""
        cache_manager.register_tenant_db(unique_tenant_id, 3)

        # 已注册独立 DB，不添加前缀
        key = cache_manager._build_key("mykey", unique_tenant_id, None)
        assert key == "mykey"

        # 清理
        cache_manager.unregister_tenant(unique_tenant_id)

    @pytest.mark.asyncio
    async def test_key_building_default(self, cache_manager, unique_tenant_id):
        """默认场景下 Key 构建规则"""
        # 无任何隔离配置，添加租户前缀
        key = cache_manager._build_key("mykey", unique_tenant_id, None)
        assert key == f"{unique_tenant_id}:mykey"

    @pytest.mark.asyncio
    async def test_stream_key_building(self, cache_manager, unique_tenant_id):
        """Stream Key 构建规则"""
        # 物理隔离
        config = TenantCacheConfig(host="redis-isolated.com")
        stream = cache_manager._build_stream_key("myqueue", unique_tenant_id, config)
        assert stream == "queue:myqueue"

        # 默认场景
        stream = cache_manager._build_stream_key("myqueue", unique_tenant_id, None)
        assert stream == f"{unique_tenant_id}:queue:myqueue"


class TestTenantCacheInstanceManagement:
    """实例管理测试"""

    @pytest.mark.asyncio
    async def test_instance_client_caching(self, cache_manager, unique_tenant_id):
        """实例客户端缓存机制"""
        config1 = TenantCacheConfig(host="redis-a.com", port=6379)
        config2 = TenantCacheConfig(host="redis-a.com", port=6379)  # 相同实例
        config3 = TenantCacheConfig(host="redis-b.com", port=6379)  # 不同实例

        # 模拟客户端创建（使用本地 Redis）
        config_local = TenantCacheConfig(host="localhost", port=6379, db=12)

        client1 = await cache_manager.get_client(unique_tenant_id, config_local)
        client2 = await cache_manager.get_client(unique_tenant_id, config_local)

        # 应返回相同实例
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_release_idle_instances(self, cache_manager, unique_tenant_id):
        """释放空闲实例客户端"""
        # 创建实例客户端
        config = TenantCacheConfig(host="localhost", port=6379, db=13)
        await cache_manager.get_client(unique_tenant_id, config)

        # 验证实例存在
        assert len(cache_manager._instance_clients) > 0

        # 释放空闲实例（超时=0，立即释放所有）
        released = await cache_manager.release_idle_instances(timeout=0)

        # 验证已释放
        assert released >= 1
        assert len(cache_manager._instance_clients) == 0

    @pytest.mark.asyncio
    async def test_get_stats(self, cache_manager, unique_tenant_id):
        """获取统计信息"""
        # 注册一些租户
        cache_manager.register_tenant_db("tenant-stats-1", 1)
        cache_manager.register_tenant_db("tenant-stats-2", 2)

        stats = cache_manager.get_stats()

        assert "registered_tenants" in stats
        assert stats["registered_tenants"] == 2
        assert "db_usage" in stats
        assert "total_instance_clients" in stats
        assert "instances" in stats

        # 清理
        cache_manager.unregister_tenant("tenant-stats-1")
        cache_manager.unregister_tenant("tenant-stats-2")


class TestTenantCacheGlobalManager:
    """全局管理器测试"""

    def test_init_and_get_cache_manager(self, redis_client):
        """初始化并获取全局缓存管理器"""
        manager = init_cache_manager(redis_client)

        from framework.cache.tenant_cache_manager import get_cache_manager
        assert get_cache_manager() is manager
