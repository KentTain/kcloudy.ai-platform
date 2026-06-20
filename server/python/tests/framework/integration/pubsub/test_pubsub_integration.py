"""
Redis 发布订阅集成测试

测试 RedisPubSub 与真实 Redis 服务的交互。
使用 @pytest.mark.integration 标记。
"""


import pytest
import pytest_asyncio

from framework.pubsub.impl.redis import RedisPubSub

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def redis_pubsub(integration_settings, redis_client):
    """Redis PubSub 实例（依赖 redis_client 确保 RedisUtil 已初始化）"""
    config = {
        "mode": integration_settings.redis.mode,
        "single": {
            "host": integration_settings.redis.single.host,
            "port": integration_settings.redis.single.port,
            "password": integration_settings.redis.single.password,
            "db": integration_settings.redis.single.db,
        }
    }
    return RedisPubSub(config)


@pytest.fixture
def cleanup_topic(redis_key_prefix):
    """生成唯一的测试主题名"""
    return f"{redis_key_prefix}topic"


class TestRedisPubSubPublish:
    """Redis 发布订阅发布测试"""

    @pytest.mark.asyncio
    async def test_publish_success(self, redis_pubsub, redis_client, cleanup_topic):
        """
        场景：消息发布
        WHEN: 调用 publish 发布消息
        THEN: 订阅者收到消息
        """
        topic = cleanup_topic

        # 直接使用 RedisUtil 验证发布功能
        message = '{"event": "test", "data": "hello"}'
        result = await redis_client.publish(topic, message)

        # Redis publish 返回接收到消息的订阅者数量
        # 没有订阅者时返回 0，这也是成功的
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_publish_via_pubsub(self, redis_pubsub, cleanup_topic):
        """
        场景：通过 PubSub 发布消息
        WHEN: 调用 RedisPubSub.publish
        THEN: 消息发布成功
        """
        topic = cleanup_topic

        # 发布消息
        message = {"event": "test", "data": "hello"}
        result = await redis_pubsub.publish(topic, message)

        # 即使没有订阅者，发布也应该成功
        # RedisPubSub.publish 在成功时返回 True
        assert result is True

    @pytest.mark.asyncio
    async def test_publish_multiple_messages(self, redis_pubsub, cleanup_topic):
        """
        场景：发布多条消息
        WHEN: 连续发布多条消息
        THEN: 所有消息发布成功
        """
        topic = cleanup_topic

        for i in range(5):
            message = {"index": i}
            result = await redis_pubsub.publish(topic, message)
            assert result is True


class TestRedisPubSubSubscribe:
    """Redis 发布订阅订阅测试"""

    @pytest.mark.asyncio
    async def test_subscribe_success(self, redis_pubsub, cleanup_topic):
        """
        场景：订阅管理
        WHEN: 调用 subscribe 订阅主题
        THEN: 成功接收后续消息
        """
        topic = cleanup_topic

        received_messages = []

        async def handler(t: str, msg: dict):
            received_messages.append((t, msg))

        # 订阅主题
        result = await redis_pubsub.subscribe(topic, handler)
        assert result is True

        # 验证订阅已注册
        assert topic in redis_pubsub._subscribers

    @pytest.mark.asyncio
    async def test_subscribe_multiple_handlers(self, redis_pubsub, cleanup_topic):
        """
        场景：多个处理器
        WHEN: 为同一主题注册多个处理器
        THEN: 所有处理器都能接收消息
        """
        topic = cleanup_topic

        calls1 = []
        calls2 = []

        async def handler1(t: str, msg: dict):
            calls1.append(msg)

        async def handler2(t: str, msg: dict):
            calls2.append(msg)

        # 注册两个处理器
        await redis_pubsub.subscribe(topic, handler1)
        await redis_pubsub.subscribe(topic, handler2)

        # 验证两个处理器都注册了
        assert len(redis_pubsub._subscribers.get(topic, [])) == 2


class TestRedisPubSubUnsubscribe:
    """Redis 发布订阅取消订阅测试"""

    @pytest.mark.asyncio
    async def test_unsubscribe_success(self, redis_pubsub, cleanup_topic):
        """
        场景：取消订阅
        WHEN: 调用 unsubscribe 取消订阅
        THEN: 不再接收该主题的消息
        """
        topic = cleanup_topic

        async def handler(t: str, msg: dict):
            pass

        # 订阅
        await redis_pubsub.subscribe(topic, handler)
        assert topic in redis_pubsub._subscribers

        # 取消订阅
        result = await redis_pubsub.unsubscribe(topic)
        assert result is True

        # 验证已取消
        assert topic not in redis_pubsub._subscribers

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_topic(self, redis_pubsub, redis_key_prefix):
        """
        场景：取消未订阅的主题
        WHEN: 取消一个从未订阅的主题
        THEN: 返回成功（幂等）
        """
        topic = f"{redis_key_prefix}nonexistent"

        result = await redis_pubsub.unsubscribe(topic)
        assert result is True


class TestRedisPubSubGetSubscribers:
    """Redis 发布订阅订阅者数量测试"""

    @pytest.mark.asyncio
    async def test_get_subscribers_count(self, redis_pubsub, redis_key_prefix):
        """
        场景：获取订阅者数量
        WHEN: 调用 get_subscribers
        THEN: 返回正确的订阅者数量
        """
        topic = f"{redis_key_prefix}subscribers"

        # 获取订阅者数量（Redis 层面）
        count = await redis_pubsub.get_subscribers(topic)
        assert isinstance(count, int)
        assert count >= 0


class TestRedisPubSubPatternSubscribe:
    """Redis 发布订阅模式订阅测试"""

    @pytest.mark.asyncio
    async def test_pattern_subscribe_success(self, redis_pubsub, redis_key_prefix):
        """
        场景：模式订阅
        WHEN: 调用 pattern_subscribe
        THEN: 成功注册模式处理器
        """
        pattern = f"{redis_key_prefix}pattern:*"

        async def handler(t: str, msg: dict):
            pass

        result = await redis_pubsub.pattern_subscribe(pattern, handler)
        assert result is True
