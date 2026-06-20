"""
Redis Stream 队列集成测试

测试 RedisQueue 与真实 Redis 服务的交互。
使用 @pytest.mark.integration 标记。
"""


import pytest
import pytest_asyncio

from framework.queue.impl.redis import RedisQueue

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def redis_queue(integration_settings):
    """Redis Stream 队列实例"""
    config = {
        "mode": integration_settings.redis.mode,
        "single": {
            "host": integration_settings.redis.single.host,
            "port": integration_settings.redis.single.port,
            "password": integration_settings.redis.single.password,
            "db": integration_settings.redis.single.db,
        }
    }
    return RedisQueue(config)


@pytest_asyncio.fixture
async def cleanup_queue(redis_client, redis_key_prefix):
    """测试后清理队列"""
    queue_name = f"{redis_key_prefix}test_queue"
    yield queue_name
    # 清理队列（添加异常处理）
    try:
        await redis_client.delete(f"queue:{queue_name}")
    except RuntimeError:
        # 事件循环可能已关闭
        pass


class TestRedisQueueEnqueue:
    """Redis Stream 队列入队测试"""

    @pytest.mark.asyncio
    async def test_enqueue_success(self, redis_queue, cleanup_queue):
        """
        场景：消息入队
        WHEN: 调用 enqueue 发送消息
        THEN: 消息成功写入 Stream
        """
        queue_name = cleanup_queue

        # 发送消息
        message = {"action": "test", "data": "hello"}
        result = await redis_queue.enqueue(queue_name, message)

        # 返回消息 ID
        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_enqueue_multiple_messages(self, redis_queue, cleanup_queue):
        """
        场景：多条消息入队
        WHEN: 连续发送多条消息
        THEN: 所有消息成功写入
        """
        queue_name = cleanup_queue

        ids = []
        for i in range(5):
            message = {"index": i}
            msg_id = await redis_queue.enqueue(queue_name, message)
            ids.append(msg_id)

        # 所有 ID 应该不同
        assert len(ids) == 5
        assert len(set(ids)) == 5


class TestRedisQueueDequeue:
    """Redis Stream 队列出队测试"""

    @pytest.mark.asyncio
    async def test_dequeue_success(self, redis_queue, cleanup_queue):
        """
        场景：消息出队
        WHEN: 调用 dequeue 读取消息
        THEN: 正确获取消息内容
        """
        queue_name = cleanup_queue

        # 先发送消息
        message = {"task": "process", "value": 42}
        await redis_queue.enqueue(queue_name, message)

        # 读取消息
        messages = await redis_queue.dequeue(queue_name, count=1)

        assert len(messages) == 1
        assert messages[0].body == message
        assert messages[0].queue == queue_name

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self, redis_queue, redis_key_prefix):
        """
        场景：空队列出队
        WHEN: 从空队列读取消息
        THEN: 返回空列表
        """
        queue_name = f"{redis_key_prefix}empty_queue"

        # 读取空队列（不阻塞）
        messages = await redis_queue.dequeue(queue_name, count=1, timeout=0)

        assert messages == []

        # 清理
        await redis_queue.purge(queue_name)


class TestRedisQueueAck:
    """Redis Stream 队列确认测试"""

    @pytest.mark.asyncio
    async def test_ack_success(self, redis_queue, cleanup_queue):
        """
        场景：消息确认
        WHEN: 调用 ack 确认消息
        THEN: 消息标记为已处理
        """
        queue_name = cleanup_queue

        # 发送并读取消息
        await redis_queue.enqueue(queue_name, {"data": "test"})
        messages = await redis_queue.dequeue(queue_name, count=1)

        assert len(messages) == 1
        message = messages[0]

        # 确认消息
        if message.metadata and "redis_id" in message.metadata:
            result = await redis_queue.ack(queue_name, message.metadata["redis_id"])
            assert result is True


class TestRedisQueueLength:
    """Redis Stream 队列长度测试"""

    @pytest.mark.asyncio
    async def test_get_queue_length(self, redis_queue, cleanup_queue):
        """
        场景：队列长度
        WHEN: 调用 get_queue_length
        THEN: 返回正确的队列长度
        """
        queue_name = cleanup_queue

        # 发送消息（Stream 会自动创建）
        await redis_queue.enqueue(queue_name, {"msg": 1})
        await redis_queue.enqueue(queue_name, {"msg": 2})

        # 检查长度
        length = await redis_queue.get_queue_length(queue_name)
        assert length == 2


class TestRedisQueuePurge:
    """Redis Stream 队列清空测试"""

    @pytest.mark.asyncio
    async def test_purge_queue(self, redis_queue, redis_key_prefix):
        """
        场景：清空队列
        WHEN: 调用 purge 清空队列
        THEN: 队列被清空
        """
        queue_name = f"{redis_key_prefix}purge_test"

        # 发送消息
        await redis_queue.enqueue(queue_name, {"msg": 1})
        await redis_queue.enqueue(queue_name, {"msg": 2})

        # 验证有消息
        length = await redis_queue.get_queue_length(queue_name)
        assert length == 2

        # 清空队列
        result = await redis_queue.purge(queue_name)
        assert result is True

        # 验证队列已空（需要重新发送消息来检查）
        await redis_queue.enqueue(queue_name, {"check": True})
        length = await redis_queue.get_queue_length(queue_name)
        assert length == 1

        # 清理
        await redis_queue.purge(queue_name)


class TestRedisQueueConsumerGroup:
    """Redis Stream 队列消费者组测试"""

    @pytest.mark.asyncio
    async def test_create_consumer_group(self, redis_queue, redis_key_prefix):
        """
        场景：创建消费者组
        WHEN: 调用 create_consumer_group
        THEN: 成功创建消费者组
        """
        queue_name = f"{redis_key_prefix}group_test"
        group_name = "test_group"

        # 创建消费者组
        result = await redis_queue.create_consumer_group(queue_name, group_name)
        assert result is True

        # 清理
        await redis_queue.purge(queue_name)
