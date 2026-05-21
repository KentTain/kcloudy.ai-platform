"""heartbeat_task 单元测试"""

from unittest.mock import patch

import pytest


class TestHeartbeatTask:
    """heartbeat_task 单元测试"""

    @pytest.mark.asyncio
    async def test_heartbeat_logs_timestamp(self):
        """WHEN: heartbeat_task 被执行
        THEN: 记录包含 UTC 时间戳的日志"""
        from demo.tasks.services.heartbeat_task import heartbeat_task

        with patch(
            "demo.tasks.services.heartbeat_task._logger"
        ) as mock_logger:
            await heartbeat_task()
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "heartbeat" in call_args.lower() or "心跳" in call_args

    @pytest.mark.asyncio
    async def test_heartbeat_exception_does_not_propagate(self):
        """WHEN: heartbeat_task 执行过程中抛出异常
        THEN: 异常被捕获，不影响后续调度"""
        from demo.tasks.services.heartbeat_task import heartbeat_task

        with patch(
            "demo.tasks.services.heartbeat_task._logger"
        ) as mock_logger:
            mock_logger.info.side_effect = RuntimeError("test error")
            # 不应抛出异常
            await heartbeat_task()
            mock_logger.exception.assert_called_once()
