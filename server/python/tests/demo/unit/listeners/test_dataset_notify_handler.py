"""DatasetNotifyHandler 单元测试"""

from datetime import datetime
from unittest.mock import patch

import pytest

from framework.core.queue import Message
from framework.queue.handler import SingleQueueHandler


class TestDatasetNotifyHandler:
    """DatasetNotifyHandler 单元测试"""

    def test_inherits_single_queue_handler(self):
        """WHEN: 实例化 DatasetNotifyHandler
        THEN: 是 SingleQueueHandler 的子类"""
        from demo.listeners.services.queue.dataset_notify_handler import (
            DatasetNotifyHandler,
        )

        handler = DatasetNotifyHandler()
        assert isinstance(handler, SingleQueueHandler)

    def test_queue_is_dataset_notify_queue(self):
        """WHEN: 获取 handler 的 queue
        THEN: 返回 DATASET_NOTIFY_QUEUE 常量"""
        from demo.listeners.services.queue.constants import (
            DATASET_NOTIFY_QUEUE,
        )
        from demo.listeners.services.queue.dataset_notify_handler import (
            DatasetNotifyHandler,
        )

        handler = DatasetNotifyHandler()
        assert handler.queue == DATASET_NOTIFY_QUEUE
        assert handler.queue == "demo:dataset:notify"

    @pytest.mark.asyncio
    async def test_handle_dataset_notify(self):
        """WHEN: 收到包含 dataset_id 的数据集通知
        THEN: 记录包含消息 body 的日志"""
        from demo.listeners.services.queue.dataset_notify_handler import (
            DatasetNotifyHandler,
        )

        handler = DatasetNotifyHandler()
        messages = [
            Message(
                id="msg-1",
                body={"dataset_id": "ds-123", "action": "created"},
                queue="demo:dataset:notify",
                timestamp=datetime.now(),
            )
        ]

        with patch(
            "demo.listeners.services.queue.dataset_notify_handler._logger"
        ) as mock_logger:
            await handler.handle("demo:dataset:notify", messages)
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "ds-123" in call_args

    @pytest.mark.asyncio
    async def test_handle_missing_dataset_id(self):
        """WHEN: 消息 body 不含 dataset_id 字段
        THEN: 记录警告日志，跳过处理，不抛异常"""
        from demo.listeners.services.queue.dataset_notify_handler import (
            DatasetNotifyHandler,
        )

        handler = DatasetNotifyHandler()
        messages = [
            Message(
                id="msg-2",
                body={"action": "unknown"},
                queue="demo:dataset:notify",
                timestamp=datetime.now(),
            )
        ]

        with patch(
            "demo.listeners.services.queue.dataset_notify_handler._logger"
        ) as mock_logger:
            await handler.handle("demo:dataset:notify", messages)
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "dataset_id" in call_args
