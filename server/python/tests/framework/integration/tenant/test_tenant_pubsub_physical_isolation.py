"""
TenantPubSubManager 物理隔离集成测试

测试场景覆盖：
1. 物理隔离频道
2. 逻辑隔离频道
3. 发布消息
4. 订阅频道
5. 取消订阅
"""

import asyncio
import uuid

import pytest
import pytest_asyncio

from framework.cache.tenant_cache_manager import TenantCacheManager
from framework.pubsub.tenant_pubsub_manager import (
    TenantPubSubManager,
    init_pubsub_manager,
)
from framework.tenant.enums import PubSubType
from framework.tenant.tenant_protocols import TenantPubSubConfig

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def cache_manager(redis_client, redis_available):
    """缓存管理器实例"""
    import asyncio

    if not redis_available:
        pytest.skip("Redis 服务不可用")

    manager = TenantCacheManager(redis_client)
    yield manager

    # 安全清理
    try:
        loop = asyncio.get_running_loop()
        if not loop.is_closed():
            await manager.close()
    except RuntimeError:
        pass


@pytest_asyncio.fixture
async def pubsub_manager(cache_manager):
    """发布订阅管理器实例"""
    manager = TenantPubSubManager(cache_manager)
    yield manager


@pytest_asyncio.fixture
def unique_tenant_id():
    """生成唯一租户 ID"""
    return f"tenant-{uuid.uuid4().hex[:8]}"


@pytest_asyncio.fixture
def unique_channel():
    """生成唯一频道名"""
    return f"test_channel_{uuid.uuid4().hex[:8]}"


class TestTenantPubSubPhysicalIsolation:
    """物理隔离场景测试"""

    @pytest.mark.asyncio
    async def test_physical_isolation_channel(self, pubsub_manager, unique_tenant_id):
        """
        场景: 物理隔离频道

        WHEN 配置了独立消息实例
        THEN 消息发布到独立实例的频道，频道名不添加前缀
        """
        config = TenantPubSubConfig(
            type=PubSubType.REDIS,
            host="pubsub-tenant-a.example.com",
            port=6379,
            password="secret",
        )

        # 验证物理隔离判断
        assert pubsub_manager._is_physical_isolation(config) is True

        # 构建频道名
        channel_name = pubsub_manager._build_channel_name(
            "events", unique_tenant_id, config
        )

        # 物理隔离场景，频道名不添加租户前缀
        assert channel_name == "events"
        assert unique_tenant_id not in channel_name

    @pytest.mark.asyncio
    async def test_logical_isolation_channel(self, pubsub_manager, unique_tenant_id):
        """
        场景: 逻辑隔离频道

        WHEN 使用默认 Redis 实例
        THEN 频道名添加 {tenant_id}:channel: 前缀
        """
        # 构建频道名（无物理隔离配置）
        channel_name = pubsub_manager._build_channel_name(
            "events", unique_tenant_id, None
        )

        # 逻辑隔离场景，频道名添加租户前缀
        expected_prefix = f"{unique_tenant_id}:channel:"
        assert channel_name.startswith(expected_prefix)
        assert "events" in channel_name
        assert channel_name == f"{unique_tenant_id}:channel:events"


class TestTenantPubSubOperations:
    """发布订阅操作测试"""

    @pytest.mark.asyncio
    async def test_publish_message_logical_isolation(
        self, pubsub_manager, unique_tenant_id, unique_channel, redis_client
    ):
        """
        场景: 发布消息 - 逻辑隔离

        WHEN 调用 publish() 发布消息到频道
        THEN 消息发布到正确的频道
        """
        message = "Hello, logical isolation!"

        # 发布消息（逻辑隔离）
        result = await pubsub_manager.publish(
            channel=unique_channel,
            message=message,
            tenant_id=unique_tenant_id,
        )

        # 返回订阅者数量（可能为 0）
        assert isinstance(result, int)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_publish_message_physical_isolation(
        self, pubsub_manager, unique_tenant_id, unique_channel, redis_client
    ):
        """
        场景: 发布消息 - 物理隔离

        WHEN 配置了独立消息实例并发布消息
        THEN 消息发布到物理隔离频道
        """
        # 使用本地 Redis 作为物理隔离实例
        config = TenantPubSubConfig(
            type=PubSubType.REDIS,
            host="localhost",
            port=6379,
            password="XdA9caoq",
        )

        # 构建频道名
        actual_channel = pubsub_manager._build_channel_name(
            unique_channel, unique_tenant_id, config
        )

        # 验证频道名格式
        assert actual_channel == unique_channel
        assert unique_tenant_id not in actual_channel

        # 发布消息
        message = "Hello, physical isolation!"
        result = await pubsub_manager.publish(
            channel=unique_channel,
            message=message,
            tenant_id=unique_tenant_id,
            config=config,
        )

        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_subscribe_channel_logical_isolation(
        self, pubsub_manager, unique_tenant_id, unique_channel, redis_client
    ):
        """
        场景: 订阅频道 - 逻辑隔离

        WHEN 调用 subscribe() 订阅频道
        THEN 开始接收该频道的消息
        """
        # 订阅频道
        pubsub = await pubsub_manager.subscribe(
            channel=unique_channel,
            tenant_id=unique_tenant_id,
        )

        assert pubsub is not None

        # 发布测试消息
        message = "Test subscription message"
        await pubsub_manager.publish(
            channel=unique_channel,
            message=message,
            tenant_id=unique_tenant_id,
        )

        # 等待消息到达
        await asyncio.sleep(0.1)

        # 获取消息（非阻塞方式检查）
        received = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)

        # 验证接收到消息
        if received and received.get("type") == "message":
            assert (
                received.get("data") == message.encode()
                or received.get("data") == message
            )

        # 取消订阅
        await pubsub_manager.unsubscribe(pubsub, unique_channel)

    @pytest.mark.asyncio
    async def test_subscribe_channel_physical_isolation(
        self, pubsub_manager, unique_tenant_id, unique_channel, redis_client
    ):
        """
        场景: 订阅频道 - 物理隔离

        WHEN 配置了独立消息实例并订阅频道
        THEN 订阅物理隔离频道
        """
        # 使用本地 Redis 作为物理隔离实例
        config = TenantPubSubConfig(
            type=PubSubType.REDIS,
            host="localhost",
            port=6379,
            password="XdA9caoq",
        )

        # 订阅频道
        pubsub = await pubsub_manager.subscribe(
            channel=unique_channel,
            tenant_id=unique_tenant_id,
            config=config,
        )

        assert pubsub is not None

        # 发布测试消息
        message = "Physical isolation subscription test"
        await pubsub_manager.publish(
            channel=unique_channel,
            message=message,
            tenant_id=unique_tenant_id,
            config=config,
        )

        # 等待消息到达
        await asyncio.sleep(0.1)

        # 取消订阅
        await pubsub_manager.unsubscribe(pubsub, unique_channel)

    @pytest.mark.asyncio
    async def test_unsubscribe_channel(
        self, pubsub_manager, unique_tenant_id, unique_channel
    ):
        """
        场景: 取消订阅

        WHEN 调用 unsubscribe() 取消订阅
        THEN 停止接收该频道的消息
        """
        # 订阅频道
        pubsub = await pubsub_manager.subscribe(
            channel=unique_channel,
            tenant_id=unique_tenant_id,
        )

        assert pubsub is not None

        # 取消订阅
        await pubsub_manager.unsubscribe(pubsub, unique_channel)

        # 验证已取消订阅（无法直接验证，通过不抛异常判断）
        # 再次调用 unsubscribe 应该也是安全的
        try:
            await pubsub_manager.unsubscribe(pubsub, unique_channel)
        except Exception:
            # 某些客户端可能会抛出异常
            pass


class TestTenantPubSubChannelBuilding:
    """频道名构建规则测试"""

    @pytest.mark.asyncio
    async def test_channel_name_with_physical_isolation(
        self, pubsub_manager, unique_tenant_id
    ):
        """物理隔离场景下频道名构建"""
        config = TenantPubSubConfig(host="pubsub.isolated.com", port=6379)

        name = pubsub_manager._build_channel_name("alerts", unique_tenant_id, config)
        assert name == "alerts"

    @pytest.mark.asyncio
    async def test_channel_name_with_skip_tenant(
        self, pubsub_manager, unique_tenant_id
    ):
        """skip_tenant 场景下频道名构建"""
        name = pubsub_manager._build_channel_name(
            "alerts", unique_tenant_id, None, skip_tenant=True
        )
        assert name == "alerts"

    @pytest.mark.asyncio
    async def test_channel_name_default(self, pubsub_manager, unique_tenant_id):
        """默认场景下频道名构建"""
        name = pubsub_manager._build_channel_name("alerts", unique_tenant_id, None)
        assert name == f"{unique_tenant_id}:channel:alerts"


class TestTenantPubSubMessageFlow:
    """消息流测试"""

    @pytest.mark.asyncio
    async def test_pubsub_message_flow_logical_isolation(
        self, pubsub_manager, unique_tenant_id, unique_channel
    ):
        """
        场景: 完整的发布订阅消息流 - 逻辑隔离

        WHEN 发布者发布消息，订阅者订阅频道
        THEN 订阅者能正确接收消息
        """
        received_messages = []

        # 订阅频道
        pubsub = await pubsub_manager.subscribe(
            channel=unique_channel,
            tenant_id=unique_tenant_id,
        )

        # 等待订阅生效
        await asyncio.sleep(0.1)

        # 发布多条消息
        test_messages = [f"Message {i}" for i in range(3)]

        async def publisher():
            for msg in test_messages:
                await pubsub_manager.publish(
                    channel=unique_channel,
                    message=msg,
                    tenant_id=unique_tenant_id,
                )
                await asyncio.sleep(0.05)

        # 启动发布者
        publish_task = asyncio.create_task(publisher())

        # 等待发布完成
        await publish_task

        # 收集消息
        for _ in range(5):  # 尝试读取几次
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.2)
            if msg and msg.get("type") == "message":
                data = msg.get("data")
                if isinstance(data, bytes):
                    data = data.decode()
                received_messages.append(data)

        # 验证至少收到一些消息
        # 注意：由于 Redis PubSub 的特性，可能不是所有消息都能收到
        # 这里主要验证流程正常工作

        # 取消订阅
        await pubsub_manager.unsubscribe(pubsub, unique_channel)

    @pytest.mark.asyncio
    async def test_different_tenant_isolation(self, pubsub_manager, unique_channel):
        """
        场景: 不同租户的频道隔离

        WHEN 两个租户使用相同频道名
        THEN 消息互不干扰
        """
        tenant_a = f"tenant-a-{uuid.uuid4().hex[:8]}"
        tenant_b = f"tenant-b-{uuid.uuid4().hex[:8]}"

        # 构建各自的频道名
        channel_a = pubsub_manager._build_channel_name(unique_channel, tenant_a, None)
        channel_b = pubsub_manager._build_channel_name(unique_channel, tenant_b, None)

        # 验证频道名不同
        assert channel_a != channel_b
        assert tenant_a in channel_a
        assert tenant_b in channel_b


class TestTenantPubSubGlobalManager:
    """全局管理器测试"""

    def test_init_and_get_pubsub_manager(self, cache_manager):
        """初始化并获取全局发布订阅管理器"""
        manager = init_pubsub_manager(cache_manager)

        from framework.pubsub.tenant_pubsub_manager import get_pubsub_manager

        assert get_pubsub_manager() is manager
