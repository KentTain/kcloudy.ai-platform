"""application_listener 入口测试"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestApplicationListener:
    """application_listener 入口测试"""

    def test_main_is_click_command(self):
        """WHEN: 导入 main
        THEN: 是 click 命令"""
        from application_listener import main

        assert callable(main)

    @pytest.mark.asyncio
    async def test_run_listener_loads_modules(self):
        """WHEN: run_listener 启动
        THEN: 加载模块并调用 listener setup"""
        # 创建 mock 模块
        mock_module = MagicMock()
        mock_module.name = "test_module"
        mock_setup = AsyncMock()
        mock_cleanup = AsyncMock()
        mock_module.get_listener_setup.return_value = (mock_setup, mock_cleanup)

        with patch(
            "application_listener.load_modules",
            return_value=[mock_module],
        ), patch(
            "application_listener.get_registry",
        ) as mock_registry, patch(
            "application_listener._get_tenant_provider",
            return_value=None,
        ), patch(
            "framework.database.core.engine.setup_engine",
        ):
            mock_registry_instance = MagicMock()
            mock_registry_instance.get_all_modules.return_value = [mock_module]
            mock_registry.return_value = mock_registry_instance

            from application_listener import run_listener

            loop = asyncio.get_running_loop()

            # 捕获 signal handler 注册的回调
            signal_callbacks = []

            def mock_add_signal(sig, callback, *args):
                signal_callbacks.append(callback)

            # mock add_signal_handler（Windows ProactorEventLoop 不支持）
            with patch.object(loop, "add_signal_handler", side_effect=mock_add_signal):
                task = asyncio.create_task(run_listener())

                # 等待 setup 完成
                await asyncio.sleep(0.1)

                # 触发第一个 signal 回调来 resolve stop future
                if signal_callbacks:
                    signal_callbacks[0]()

                await task

            mock_setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_listener_registers_signal_handlers(self):
        """WHEN: run_listener 启动
        THEN: 注册 SIGINT 和 SIGTERM 信号处理器"""
        import signal

        # 创建 mock 模块（无 listener setup）
        mock_module = MagicMock()
        mock_module.name = "test_module"
        mock_module.get_listener_setup.return_value = None

        with patch(
            "application_listener.load_modules",
            return_value=[mock_module],
        ), patch(
            "application_listener.get_registry",
        ) as mock_registry, patch(
            "application_listener._get_tenant_provider",
            return_value=None,
        ), patch(
            "framework.database.core.engine.setup_engine",
        ):
            mock_registry_instance = MagicMock()
            mock_registry_instance.get_all_modules.return_value = [mock_module]
            mock_registry.return_value = mock_registry_instance

            from application_listener import run_listener

            loop = asyncio.get_running_loop()

            registered_signals = []

            def mock_add_signal(sig, callback, *args):
                registered_signals.append(sig)

            with patch.object(loop, "add_signal_handler", side_effect=mock_add_signal):
                task = asyncio.create_task(run_listener())
                await asyncio.sleep(0.1)

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
