"""application_listener 入口测试"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


class TestApplicationListener:
    """application_listener 入口测试"""

    def test_main_is_click_command(self):
        """WHEN: 导入 main
        THEN: 是 click 命令"""
        from application_listener import main

        assert callable(main)

    @pytest.mark.asyncio
    async def test_run_listener_calls_setup(self):
        """WHEN: run_listener 启动
        THEN: 调用 setup_listeners()"""
        with patch(
            "application_listener.setup_listeners",
            new_callable=AsyncMock,
        ) as mock_setup, patch(
            "application_listener.cleanup_listeners",
            new_callable=AsyncMock,
        ) as mock_cleanup, patch(
            "application_listener.init_settings"
        ):
            from application_listener import run_listener

            loop = asyncio.get_running_loop()

            # 捕获 signal handler 注册的回调
            signal_callbacks = []

            def mock_add_signal(sig, callback, *args):
                signal_callbacks.append(callback)

            # mock add_signal_handler（Windows ProactorEventLoop 不支持）
            with patch.object(loop, "add_signal_handler", side_effect=mock_add_signal):
                task = asyncio.create_task(run_listener())

                # 等待 setup_listeners 完成
                await asyncio.sleep(0.05)

                # 触发第一个 signal 回调来 resolve stop future
                if signal_callbacks:
                    signal_callbacks[0]()

                await task

            mock_setup.assert_called_once()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_listener_registers_signal_handlers(self):
        """WHEN: run_listener 启动
        THEN: 注册 SIGINT 和 SIGTERM 信号处理器"""
        with patch(
            "application_listener.setup_listeners",
            new_callable=AsyncMock,
        ), patch(
            "application_listener.cleanup_listeners",
            new_callable=AsyncMock,
        ), patch(
            "application_listener.init_settings"
        ):
            import signal

            from application_listener import run_listener

            loop = asyncio.get_running_loop()

            registered_signals = []

            def mock_add_signal(sig, callback, *args):
                registered_signals.append(sig)

            with patch.object(loop, "add_signal_handler", side_effect=mock_add_signal):
                task = asyncio.create_task(run_listener())
                await asyncio.sleep(0.05)

                # 触发 stop
                if registered_signals:
                    # 访问 signal_callbacks 不可用，直接 cancel
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            assert signal.SIGINT in registered_signals
            assert signal.SIGTERM in registered_signals
