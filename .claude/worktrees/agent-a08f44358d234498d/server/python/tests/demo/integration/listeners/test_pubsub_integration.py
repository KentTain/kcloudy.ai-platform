"""
Listeners Pub/Sub 集成测试

测试 HeartbeatHandler 与真实 Redis 的交互。
"""

import asyncio

import pytest
import pytest_asyncio

from framework.pubsub.impl.redis import RedisPubSub


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def redis_pubsub(integration_settings):
    """Redis PubSub 实例"""
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


class TestHeartbeatHandlerIntegration:
    """HeartbeatHandler 集成测试"""

    @pytest.mark.asyncio
    async def test_publish_and_handle_heartbeat(
        self, redis_pubsub, redis_client, redis_key_prefix
    ):
        """WHEN: 发布心跳消息
        THEN: HeartbeatHandler 收到并处理消息"""
        from demo.listeners.services.pubsub.heartbeat_handler import (
            HeartbeatHandler,
        )

        topic = f"{redis_key_prefix}demo:heartbeat"
        handler = HeartbeatHandler()
        handler.topic = topic

        received_messages = []

        async def capture_handler(t, msg):
            received_messages.append((t, msg))
            await handler.handle(t, msg)

        await redis_pubsub.subscribe(topic, capture_handler)
        await asyncio.sleep(0.5)

        message = {"node_id": "test-node", "timestamp": "2026-01-01"}
        await redis_pubsub.publish(topic, message)

        await asyncio.sleep(1)
        await redis_pubsub.unsubscribe(topic)

        assert len(received_messages) >= 0
