"""
Listeners Queue 集成测试

测试 DatasetNotifyHandler 与真实 Redis 的交互。
"""

import pytest
import pytest_asyncio

from framework.queue.impl.redis import RedisQueue

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def redis_queue(integration_settings):
    """Redis Queue 实例"""
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


class TestDatasetNotifyHandlerIntegration:
    """DatasetNotifyHandler 集成测试"""

    @pytest.mark.asyncio
    async def test_enqueue_and_handle(
        self, redis_queue, redis_key_prefix
    ):
        """WHEN: 消息入队
        THEN: 可以出队并由 handler 处理"""
        from demo.listeners.services.queue.dataset_notify_handler import (
            DatasetNotifyHandler,
        )

        queue_name = f"{redis_key_prefix}demo:dataset:notify"

        message = {"dataset_id": "ds-123", "action": "created"}
        msg_id = await redis_queue.enqueue(queue_name, message)
        assert msg_id is not None

        messages = await redis_queue.dequeue(queue_name, count=1)
        assert len(messages) == 1
        assert messages[0].body["dataset_id"] == "ds-123"

        handler = DatasetNotifyHandler()
        await handler.handle(queue_name, messages)

        await redis_queue.ack(queue_name, messages[0].id)
