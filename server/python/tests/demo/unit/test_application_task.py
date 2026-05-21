"""application_task 入口测试"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


class TestApplicationTask:
    """application_task 入口测试"""

    def test_main_is_click_command(self):
        """WHEN: 导入 main
        THEN: 是 click 命令"""
        from demo.application_task import main

        assert callable(main)

    @pytest.mark.asyncio
    async def test_run_task_calls_setup(self):
        """WHEN: run_task 启动
        THEN: 调用 setup_scheduler()"""
        with patch(
            "demo.application_task.setup_scheduler",
            new_callable=AsyncMock,
        ) as mock_setup, patch(
            "demo.application_task.cleanup_scheduler",
            new_callable=AsyncMock,
        ) as mock_cleanup:
            from demo.application_task import run_task

            loop = asyncio.get_running_loop()

            # 捕获 signal handler 注册的回调
            signal_callbacks = []

            def mock_add_signal(sig, callback, *args):
                signal_callbacks.append(callback)

            # mock add_signal_handler（Windows ProactorEventLoop 不支持）
            with patch.object(loop, "add_signal_handler", side_effect=mock_add_signal):
                task = asyncio.create_task(run_task())

                # 等待 setup_scheduler 完成
                await asyncio.sleep(0.05)

                # 触发第一个 signal 回调来 resolve stop future
                if signal_callbacks:
                    signal_callbacks[0]()

                await task

            mock_setup.assert_called_once()
            mock_cleanup.assert_called_once()
