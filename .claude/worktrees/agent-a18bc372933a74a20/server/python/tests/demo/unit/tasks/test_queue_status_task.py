"""queue_status_task 单元测试"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestQueueStatusTask:
    """queue_status_task 单元测试"""

    @pytest.mark.asyncio
    async def test_queue_has_messages(self):
        """WHEN: 队列中有待处理消息
        THEN: 记录包含队列名称和消息数的日志"""
        from demo.tasks.services.queue_status_task import (
            queue_status_task,
        )

        mock_queue = AsyncMock()
        mock_queue.get_queue_length = AsyncMock(return_value=5)

        with (
            patch(
                "demo.tasks.services.queue_status_task.get_queue_provider",
                return_value=mock_queue,
            ),
            patch(
                "demo.tasks.services.queue_status_task._logger"
            ) as mock_logger,
        ):
            await queue_status_task()
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "5" in call_args

    @pytest.mark.asyncio
    async def test_queue_is_empty(self):
        """WHEN: 队列为空
        THEN: 记录队列为空的日志"""
        from demo.tasks.services.queue_status_task import (
            queue_status_task,
        )

        mock_queue = AsyncMock()
        mock_queue.get_queue_length = AsyncMock(return_value=0)

        with (
            patch(
                "demo.tasks.services.queue_status_task.get_queue_provider",
                return_value=mock_queue,
            ),
            patch(
                "demo.tasks.services.queue_status_task._logger"
            ) as mock_logger,
        ):
            await queue_status_task()
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "0" in call_args

    @pytest.mark.asyncio
    async def test_queue_provider_unavailable(self):
        """WHEN: QueueProvider 不可用
        THEN: 异常被捕获，记录错误日志，不影响后续调度"""
        from demo.tasks.services.queue_status_task import (
            queue_status_task,
        )

        with (
            patch(
                "demo.tasks.services.queue_status_task.get_queue_provider",
                side_effect=RuntimeError("connection refused"),
            ),
            patch(
                "demo.tasks.services.queue_status_task._logger"
            ) as mock_logger,
        ):
            await queue_status_task()
            mock_logger.exception.assert_called_once()
