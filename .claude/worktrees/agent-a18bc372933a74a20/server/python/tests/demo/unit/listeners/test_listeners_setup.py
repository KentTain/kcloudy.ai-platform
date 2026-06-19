"""Listeners setup/cleanup 生命周期测试"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSetupListeners:
    """setup_listeners 测试"""

    @pytest.mark.asyncio
    async def test_setup_registers_pubsub_handler(self):
        """WHEN: 调用 setup_listeners()
        THEN: 注册 HeartbeatHandler 到 PubSubProvider"""
        mock_pubsub = AsyncMock()
        mock_queue = AsyncMock()
        mock_settings = MagicMock()

        with (
            patch(
                "demo.listeners.setup.get_pubsub_provider",
                return_value=mock_pubsub,
            ),
            patch(
                "demo.listeners.setup.get_queue_provider",
                return_value=mock_queue,
            ),
        ):
            from demo.listeners.setup import setup_listeners

            await setup_listeners(mock_settings)

            # 验证 pubsub subscribe 被调用
            mock_pubsub.subscribe.assert_called_once()
            call_args = mock_pubsub.subscribe.call_args
            assert call_args[0][0] == "demo:heartbeat"

    @pytest.mark.asyncio
    async def test_setup_registers_queue_handler(self):
        """WHEN: 调用 setup_listeners()
        THEN: 注册 DatasetNotifyHandler 到 QueueProvider"""
        mock_pubsub = AsyncMock()
        mock_queue = AsyncMock()
        mock_settings = MagicMock()

        with (
            patch(
                "demo.listeners.setup.get_pubsub_provider",
                return_value=mock_pubsub,
            ),
            patch(
                "demo.listeners.setup.get_queue_provider",
                return_value=mock_queue,
            ),
        ):
            from demo.listeners.setup import setup_listeners

            await setup_listeners(mock_settings)

            # 验证 queue consumer group 被创建
            mock_queue.create_consumer_group.assert_called_once()


class TestCleanupListeners:
    """cleanup_listeners 测试"""

    @pytest.mark.asyncio
    async def test_cleanup_unsubscribes_all(self):
        """WHEN: 调用 cleanup_listeners()
        THEN: 取消所有订阅"""
        mock_pubsub = AsyncMock()
        mock_queue = AsyncMock()

        with (
            patch(
                "demo.listeners.setup._pubsub_provider",
                mock_pubsub,
                create=True,
            ),
            patch(
                "demo.listeners.setup._queue_provider",
                mock_queue,
                create=True,
            ),
        ):
            from demo.listeners.setup import cleanup_listeners

            await cleanup_listeners()

            mock_pubsub.unsubscribe.assert_called_once_with("demo:heartbeat")
