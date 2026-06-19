"""HeartbeatHandler 单元测试"""

from unittest.mock import AsyncMock, patch

import pytest

from framework.pubsub.handler import SingleTopicHandler


class TestHeartbeatHandler:
    """HeartbeatHandler 单元测试"""

    def test_inherits_single_topic_handler(self):
        """WHEN: 实例化 HeartbeatHandler
        THEN: 是 SingleTopicHandler 的子类"""
        from demo.listeners.services.pubsub.heartbeat_handler import (
            HeartbeatHandler,
        )

        handler = HeartbeatHandler()
        assert isinstance(handler, SingleTopicHandler)

    def test_topic_is_heartbeat_topic(self):
        """WHEN: 获取 handler 的 topic
        THEN: 返回 HEARTBEAT_TOPIC 常量"""
        from demo.listeners.services.pubsub.constants import (
            HEARTBEAT_TOPIC,
        )
        from demo.listeners.services.pubsub.heartbeat_handler import (
            HeartbeatHandler,
        )

        handler = HeartbeatHandler()
        assert handler.topic == HEARTBEAT_TOPIC
        assert handler.topic == "demo:heartbeat"

    @pytest.mark.asyncio
    async def test_handle_heartbeat_message(self):
        """WHEN: 收到心跳消息
        THEN: 记录包含消息 payload 的日志"""
        from demo.listeners.services.pubsub.heartbeat_handler import (
            HeartbeatHandler,
        )

        handler = HeartbeatHandler()
        message = {"node_id": "test-node", "timestamp": "2026-01-01"}

        with patch(
            "demo.listeners.services.pubsub.heartbeat_handler._logger"
        ) as mock_logger:
            await handler.handle("demo:heartbeat", message)
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "demo:heartbeat" in call_args
            assert "test-node" in call_args

    @pytest.mark.asyncio
    async def test_handle_empty_payload(self):
        """WHEN: 收到空 payload 的消息
        THEN: 记录日志，不抛出异常"""
        from demo.listeners.services.pubsub.heartbeat_handler import (
            HeartbeatHandler,
        )

        handler = HeartbeatHandler()
        message = {}

        with patch(
            "demo.listeners.services.pubsub.heartbeat_handler._logger"
        ) as mock_logger:
            await handler.handle("demo:heartbeat", message)
            mock_logger.info.assert_called_once()
