"""
安装任务执行器单元测试

验证 Path B（异步任务安装）调用统一安装编排的委托关系：
- 成功路径：下载插件包 → 获取 PluginManager → 调用 install_plugin（统一编排）
- 任务数据不完整：提前返回
- 下载失败：标记任务 failed + 发布失败事件
- 安装编排抛异常：标记任务 failed + 发布失败事件
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.listeners.services.queue.install_task_executor import InstallTaskExecutor


def _make_task_data(plugin_id: str = "test/plugin") -> dict:
    return {
        "task_id": "task-123",
        "tenant_id": "test-tenant",
        "plugin_id": plugin_id,
        "plugin_unique_identifier": "test/plugin:1.0.0@abc123",
        "auto_start": False,
    }


def _patch_session(session: MagicMock):
    """构造 get_task_session 异步上下文管理器 mock"""

    @asynccontextmanager
    async def _fake_session():
        yield session

    return _fake_session


class TestInstallTaskExecutorExecute:
    """执行器 execute() 委托统一编排测试"""

    @pytest.mark.asyncio
    async def test_execute_success_delegates_to_unified_orchestration(self):
        """成功路径：应下载插件包并调用 plugin_manager.install_plugin 统一编排"""
        mock_session = MagicMock()
        mock_plugin_manager = MagicMock()
        mock_plugin_manager.install_plugin = AsyncMock()

        with patch(
            "ai.listeners.services.queue.install_task_executor.get_task_session",
            _patch_session(mock_session),
        ), patch(
            "ai.listeners.services.queue.install_task_executor.install_task_service.update_task_status",
            new_callable=AsyncMock,
        ), patch(
            "ai.listeners.services.queue.install_task_executor.install_task_service.update_task_step",
            new_callable=AsyncMock,
        ), patch(
            "ai.listeners.services.queue.install_task_executor.plugin_storage_service.download_package",
            new_callable=AsyncMock,
            return_value=b"fake-package-bytes",
        ), patch(
            "ai.components.plugin.engine.core.plugin_manager.PluginManagerFactory.get_manager",
            new_callable=AsyncMock,
            return_value=mock_plugin_manager,
        ):
            executor = InstallTaskExecutor()
            await executor.execute(_make_task_data())

        # 核心断言：调用统一安装编排，传入下载的插件包字节与 auto_start
        mock_plugin_manager.install_plugin.assert_awaited_once()
        call = mock_plugin_manager.install_plugin.call_args
        assert call.args[0] is mock_session
        assert call.kwargs["plugin_package"] == b"fake-package-bytes"
        install_request = call.kwargs["install_request"]
        assert install_request.auto_start is False

    @pytest.mark.asyncio
    async def test_execute_missing_task_data_returns_early(self):
        """任务数据不完整时应提前返回，不创建 session"""
        incomplete_data = {
            "task_id": "task-123",
            # 缺少 tenant_id 和 plugin_id
        }

        with patch(
            "ai.listeners.services.queue.install_task_executor.get_task_session"
        ) as mock_get_session, patch(
            "ai.listeners.services.queue.install_task_executor.plugin_storage_service.download_package",
            new_callable=AsyncMock,
        ) as mock_download:
            executor = InstallTaskExecutor()
            await executor.execute(incomplete_data)

        # 数据不完整时不应进入 session 上下文，也不应下载插件包
        mock_get_session.assert_not_called()
        mock_download.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_package_not_found_marks_failed_and_publishes_event(self):
        """下载插件包失败（返回 None）应标记任务 failed 并发布失败事件"""
        mock_session = MagicMock()

        with patch(
            "ai.listeners.services.queue.install_task_executor.get_task_session",
            _patch_session(mock_session),
        ), patch(
            "ai.listeners.services.queue.install_task_executor.install_task_service.update_task_status",
            new_callable=AsyncMock,
        ) as mock_update_status, patch(
            "ai.listeners.services.queue.install_task_executor.install_task_service.update_task_step",
            new_callable=AsyncMock,
        ), patch(
            "ai.listeners.services.queue.install_task_executor.plugin_storage_service.download_package",
            new_callable=AsyncMock,
            return_value=None,  # 下载失败
        ), patch.object(
            InstallTaskExecutor, "_publish_installation_failed_event",
            new_callable=AsyncMock,
        ) as mock_publish:
            executor = InstallTaskExecutor()
            await executor.execute(_make_task_data())

        # 应更新任务状态为 failed
        failed_call = mock_update_status.call_args_list[-1]
        assert failed_call.kwargs.get("status") == "failed"
        assert failed_call.kwargs.get("error_message") is not None

        # 应发布安装失败事件
        mock_publish.assert_awaited_once()
        call_args = mock_publish.call_args
        assert call_args.args[1] == "test/plugin"  # plugin_id

    @pytest.mark.asyncio
    async def test_execute_install_raises_marks_failed_and_publishes_event(self):
        """统一编排抛异常时应标记任务 failed 并发布失败事件"""
        mock_session = MagicMock()
        mock_plugin_manager = MagicMock()
        mock_plugin_manager.install_plugin = AsyncMock(
            side_effect=RuntimeError("安装编排失败")
        )

        with patch(
            "ai.listeners.services.queue.install_task_executor.get_task_session",
            _patch_session(mock_session),
        ), patch(
            "ai.listeners.services.queue.install_task_executor.install_task_service.update_task_status",
            new_callable=AsyncMock,
        ) as mock_update_status, patch(
            "ai.listeners.services.queue.install_task_executor.install_task_service.update_task_step",
            new_callable=AsyncMock,
        ), patch(
            "ai.listeners.services.queue.install_task_executor.plugin_storage_service.download_package",
            new_callable=AsyncMock,
            return_value=b"fake-package-bytes",
        ), patch(
            "ai.components.plugin.engine.core.plugin_manager.PluginManagerFactory.get_manager",
            new_callable=AsyncMock,
            return_value=mock_plugin_manager,
        ), patch.object(
            InstallTaskExecutor, "_publish_installation_failed_event",
            new_callable=AsyncMock,
        ) as mock_publish:
            executor = InstallTaskExecutor()
            await executor.execute(_make_task_data())

        # 统一编排被调用（即便后续失败）
        mock_plugin_manager.install_plugin.assert_awaited_once()

        # 应标记 failed 并发布事件
        failed_call = mock_update_status.call_args_list[-1]
        assert failed_call.kwargs.get("status") == "failed"
        assert "安装编排失败" in failed_call.kwargs.get("error_message", "")
        mock_publish.assert_awaited_once()
