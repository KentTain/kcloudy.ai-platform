"""application_task 入口测试"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestApplicationTask:
    """application_task 入口测试"""

    def test_main_is_click_command(self):
        """WHEN: 导入 main
        THEN: 是 click 命令"""
        from application_task import main

        assert callable(main)

    @pytest.mark.asyncio
    async def test_run_task_loads_modules(self):
        """WHEN: run_task 启动
        THEN: 加载模块并调用 task setup"""
        # 创建 mock 模块
        mock_module = MagicMock()
        mock_module.name = "test_module"
        mock_setup = AsyncMock()
        mock_cleanup = AsyncMock()
        mock_module.get_task_setup.return_value = (mock_setup, mock_cleanup)

        with patch(
            "application_task.load_modules",
            return_value=[mock_module],
        ), patch(
            "application_task.get_registry",
        ) as mock_registry, patch(
            "application_task._get_tenant_provider",
            return_value=None,
        ), patch(
            "framework.database.core.engine.setup_engine",
        ):
            mock_registry_instance = MagicMock()
            mock_registry_instance.get_all_modules.return_value = [mock_module]
            mock_registry.return_value = mock_registry_instance

            from application_task import run_task

            loop = asyncio.get_running_loop()

            # 捕获 signal handler 注册的回调
            signal_callbacks = []

            def mock_add_signal(sig, callback, *args):
                signal_callbacks.append(callback)

            # mock add_signal_handler（Windows ProactorEventLoop 不支持）
            with patch.object(loop, "add_signal_handler", side_effect=mock_add_signal):
                task = asyncio.create_task(run_task())

                # 等待 setup 完成
                await asyncio.sleep(0.1)

                # 触发第一个 signal 回调来 resolve stop future
                if signal_callbacks:
                    signal_callbacks[0]()

                await task

            mock_setup.assert_called_once()
            mock_cleanup.assert_called_once()
