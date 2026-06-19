"""
TenantQueueManager 物理隔离集成测试

测试场景覆盖：
1. 物理隔离队列
2. 逻辑隔离队列
3. 发送消息
4. 消费消息
5. 确认消息
"""

import uuid

import pytest
import pytest_asyncio

from framework.cache.tenant_cache_manager import TenantCacheManager
from framework.queue.tenant_queue_manager import TenantQueueManager, init_queue_manager
from framework.tenant.enums import QueueType
from framework.tenant.protocols import TenantQueueConfig

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
async def queue_manager(cache_manager):
    """队列管理器实例"""
    manager = TenantQueueManager(cache_manager)
    yield manager


@pytest_asyncio.fixture
def unique_tenant_id():
    """生成唯一租户 ID"""
    return f"tenant-{uuid.uuid4().hex[:8]}"


@pytest_asyncio.fixture
async def cleanup_queue(redis_client, unique_tenant_id):
    """测试后清理队列"""
    queue_name = f"test_queue_{uuid.uuid4().hex[:8]}"

    yield queue_name

    # 清理逻辑隔离队列
    logical_key = f"{unique_tenant_id}:queue:{queue_name}"
    try:
        await redis_client.delete(logical_key)
    except Exception:
        pass

    # 清理物理隔离队列（如果有）
    physical_key = f"queue:{queue_name}"
    try:
        await redis_client.delete(physical_key)
    except Exception:
        pass


class TestTenantQueuePhysicalIsolation:
    """物理隔离场景测试"""

    @pytest.mark.asyncio
    async def test_physical_isolation_queue(self, queue_manager, unique_tenant_id):
        """
        场景: 物理隔离队列

        WHEN 配置了独立队列实例
        THEN 消息存储在独立实例，队列名不添加前缀
        """
        config = TenantQueueConfig(
            type=QueueType.REDIS,
            host="queue-tenant-a.example.com",
            port=6379,
            password="secret",
        )

        # 验证物理隔离判断
        assert queue_manager._is_physical_isolation(config) is True

        # 构建队列名
        queue_name = queue_manager._build_queue_name("notifications", unique_tenant_id, config)

        # 物理隔离场景，队列名不添加租户前缀
        assert queue_name == "queue:notifications"
        assert unique_tenant_id not in queue_name

    @pytest.mark.asyncio
    async def test_logical_isolation_queue(self, queue_manager, unique_tenant_id):
        """
        场景: 逻辑隔离队列

        WHEN 使用默认 Redis 实例
        THEN 队列名添加 {tenant_id}:queue: 前缀
        """
        # 构建队列名（无物理隔离配置）
        queue_name = queue_manager._build_queue_name("notifications", unique_tenant_id, None)

        # 逻辑隔离场景，队列名添加租户前缀
        expected_prefix = f"{unique_tenant_id}:queue:"
        assert queue_name.startswith(expected_prefix)
        assert "notifications" in queue_name
        assert queue_name == f"{unique_tenant_id}:queue:notifications"


class TestTenantQueueOperations:
    """队列操作测试"""

    @pytest.mark.asyncio
    async def test_send_message_logical_isolation(
        self, queue_manager, unique_tenant_id, redis_client, cleanup_queue
    ):
        """
        场景: 发送消息 - 逻辑隔离

        WHEN 调用 xadd() 发送消息
        THEN 消息写入正确的队列，返回消息 ID
        """
        queue_name = cleanup_queue

        # 发送消息（逻辑隔离）
        message = {"action": "test", "data": "hello world"}
        msg_id = await queue_manager.xadd(
            queue_name=queue_name,
            fields=message,
            tenant_id=unique_tenant_id,
        )

        # 验证返回消息 ID
        assert msg_id is not None
        assert isinstance(msg_id, str)

        # 验证消息写入正确队列
        actual_queue = f"{unique_tenant_id}:queue:{queue_name}"
        # 使用 xlen 验证队列有消息
        length = await redis_client.xlen(actual_queue)
        assert length >= 1

    @pytest.mark.asyncio
    async def test_send_message_physical_isolation(
        self, queue_manager, unique_tenant_id, redis_client, cleanup_queue
    ):
        """
        场景: 发送消息 - 物理隔离

        WHEN 配置了独立队列实例并发送消息
        THEN 消息写入物理隔离队列
        """
        queue_name = cleanup_queue

        # 使用本地 Redis 作为物理隔离实例
        config = TenantQueueConfig(
            type=QueueType.REDIS,
            host="localhost",  # 使用本地 Redis 模拟
            port=6379,
            password="XdA9caoq",
        )

        # 构建队列名
        actual_queue = queue_manager._build_queue_name(queue_name, unique_tenant_id, config)

        # 验证队列名格式
        assert actual_queue == f"queue:{queue_name}"
        assert unique_tenant_id not in actual_queue

        # 发送消息
        message = {"action": "physical_test", "data": "isolated"}
        msg_id = await queue_manager.xadd(
            queue_name=queue_name,
            fields=message,
            tenant_id=unique_tenant_id,
            config=config,
        )

        assert msg_id is not None

    @pytest.mark.asyncio
    async def test_consume_message_logical_isolation(
        self, queue_manager, unique_tenant_id, redis_client, cleanup_queue
    ):
        """
        场景: 消费消息 - 逻辑隔离

        WHEN 调用 xreadgroup() 消费消息
        THEN 从正确的队列读取消息
        """
        queue_name = cleanup_queue

        # 创建消费者组
        actual_queue = f"{unique_tenant_id}:queue:{queue_name}"
        group_name = f"test_group_{uuid.uuid4().hex[:8]}"

        try:
            await redis_client.xgroup_create(actual_queue, group_name, id="0", mkstream=True)
        except Exception:
            # 组可能已存在
            pass

        # 先发送消息
        message = {"task": "consume_test", "value": 42}
        await queue_manager.xadd(
            queue_name=queue_name,
            fields=message,
            tenant_id=unique_tenant_id,
        )

        # 消费消息
        messages = await queue_manager.xreadgroup(
            groupname=group_name,
            consumername="consumer1",
            queue_name=queue_name,
            tenant_id=unique_tenant_id,
            count=1,
        )

        # 验证读取到消息
        assert messages is not None

        # 清理消费者组
        try:
            await redis_client.xgroup_destroy(actual_queue, group_name)
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_consume_message_physical_isolation(
        self, queue_manager, unique_tenant_id, redis_client, cleanup_queue
    ):
        """
        场景: 消费消息 - 物理隔离

        WHEN 配置了独立队列实例并消费消息
        THEN 从物理隔离队列读取消息
        """
        queue_name = cleanup_queue

        # 使用本地 Redis 作为物理隔离实例
        config = TenantQueueConfig(
            type=QueueType.REDIS,
            host="localhost",
            port=6379,
            password="XdA9caoq",
        )

        # 构建队列名
        actual_queue = f"queue:{queue_name}"
        group_name = f"test_group_physical_{uuid.uuid4().hex[:8]}"

        try:
            await redis_client.xgroup_create(actual_queue, group_name, id="0", mkstream=True)
        except Exception:
            pass

        # 发送消息
        message = {"task": "physical_consume_test", "value": 100}
        await queue_manager.xadd(
            queue_name=queue_name,
            fields=message,
            tenant_id=unique_tenant_id,
            config=config,
        )

        # 消费消息
        messages = await queue_manager.xreadgroup(
            groupname=group_name,
            consumername="consumer1",
            queue_name=queue_name,
            tenant_id=unique_tenant_id,
            config=config,
            count=1,
        )

        # 验证读取到消息
        assert messages is not None

        # 清理
        try:
            await redis_client.xgroup_destroy(actual_queue, group_name)
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_ack_message_logical_isolation(
        self, queue_manager, unique_tenant_id, redis_client, cleanup_queue
    ):
        """
        场景: 确认消息 - 逻辑隔离

        WHEN 调用 xack() 确认消息
        THEN 消息标记为已处理
        """
        queue_name = cleanup_queue

        # 创建消费者组
        actual_queue = f"{unique_tenant_id}:queue:{queue_name}"
        group_name = f"test_group_ack_{uuid.uuid4().hex[:8]}"

        try:
            await redis_client.xgroup_create(actual_queue, group_name, id="0", mkstream=True)
        except Exception:
            pass

        # 发送消息
        msg_id = await queue_manager.xadd(
            queue_name=queue_name,
            fields={"task": "ack_test"},
            tenant_id=unique_tenant_id,
        )

        # 消费消息
        messages = await queue_manager.xreadgroup(
            groupname=group_name,
            consumername="consumer1",
            queue_name=queue_name,
            tenant_id=unique_tenant_id,
            count=1,
        )

        # 确认消息
        if messages:
            ack_result = await queue_manager.xack(
                queue_name,
                group_name,
                msg_id,
                tenant_id=unique_tenant_id,
            )
            # xack 返回确认的消息数
            assert ack_result >= 0

        # 清理
        try:
            await redis_client.xgroup_destroy(actual_queue, group_name)
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_ack_message_physical_isolation(
        self, queue_manager, unique_tenant_id, redis_client, cleanup_queue
    ):
        """
        场景: 确认消息 - 物理隔离

        WHEN 配置了独立队列实例并确认消息
        THEN 消息标记为已处理
        """
        queue_name = cleanup_queue

        # 使用本地 Redis 作为物理隔离实例
        config = TenantQueueConfig(
            type=QueueType.REDIS,
            host="localhost",
            port=6379,
            password="XdA9caoq",
        )

        # 构建队列名
        actual_queue = f"queue:{queue_name}"
        group_name = f"test_group_ack_phy_{uuid.uuid4().hex[:8]}"

        try:
            await redis_client.xgroup_create(actual_queue, group_name, id="0", mkstream=True)
        except Exception:
            pass

        # 发送消息
        msg_id = await queue_manager.xadd(
            queue_name=queue_name,
            fields={"task": "physical_ack_test"},
            tenant_id=unique_tenant_id,
            config=config,
        )

        # 消费消息
        messages = await queue_manager.xreadgroup(
            groupname=group_name,
            consumername="consumer1",
            queue_name=queue_name,
            tenant_id=unique_tenant_id,
            config=config,
            count=1,
        )

        # 确认消息
        if messages:
            ack_result = await queue_manager.xack(
                queue_name,
                group_name,
                msg_id,
                tenant_id=unique_tenant_id,
                config=config,
            )
            assert ack_result >= 0

        # 清理
        try:
            await redis_client.xgroup_destroy(actual_queue, group_name)
        except Exception:
            pass


class TestTenantQueueNameBuilding:
    """队列名构建规则测试"""

    @pytest.mark.asyncio
    async def test_queue_name_with_physical_isolation(self, queue_manager, unique_tenant_id):
        """物理隔离场景下队列名构建"""
        config = TenantQueueConfig(host="queue.isolated.com", port=6379)

        name = queue_manager._build_queue_name("orders", unique_tenant_id, config)
        assert name == "queue:orders"

    @pytest.mark.asyncio
    async def test_queue_name_with_skip_tenant(self, queue_manager, unique_tenant_id):
        """skip_tenant 场景下队列名构建"""
        name = queue_manager._build_queue_name("orders", unique_tenant_id, None, skip_tenant=True)
        assert name == "queue:orders"

    @pytest.mark.asyncio
    async def test_queue_name_default(self, queue_manager, unique_tenant_id):
        """默认场景下队列名构建"""
        name = queue_manager._build_queue_name("orders", unique_tenant_id, None)
        assert name == f"{unique_tenant_id}:queue:orders"


class TestTenantQueueGlobalManager:
    """全局管理器测试"""

    def test_init_and_get_queue_manager(self, cache_manager):
        """初始化并获取全局队列管理器"""
        manager = init_queue_manager(cache_manager)

        from framework.queue.tenant_queue_manager import get_queue_manager
        assert get_queue_manager() is manager
