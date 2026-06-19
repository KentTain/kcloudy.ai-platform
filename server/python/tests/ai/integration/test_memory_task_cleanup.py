"""内存任务超时清理集成测试"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.listeners.services.pubsub.constants import CANCEL_ASYNCIO_TASK_TOPIC
from ai.listeners.services.pubsub.memory_task.cleanup import cleanup_task_after_timeout
from ai.listeners.services.pubsub.memory_task.constants import (
    ACTIVE_ASYNCIO_TASKS,
    ACTIVE_CLEANUP_TASKS,
    TASK_TYPE_GENERATE_LLM,
)


@pytest.fixture(autouse=True)
def cleanup_active_tasks():
    yield
    ACTIVE_ASYNCIO_TASKS.clear()
    ACTIVE_CLEANUP_TASKS.clear()


def _make_mock_pubsub_and_settings():
    mock_pubsub = AsyncMock()
    mock_pubsub.publish = AsyncMock(return_value=True)
    mock_settings = MagicMock()
    return mock_pubsub, mock_settings


class TestCleanupTaskAfterTimeout:
    @pytest.mark.asyncio
    async def test_cleanup_publishes_cancel_after_timeout(self):
        """超时后应发布取消信号"""
        mock_pubsub, mock_settings = _make_mock_pubsub_and_settings()

        async def long_running_task():
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                return "cancelled"

        task = asyncio.create_task(long_running_task())
        await asyncio.sleep(0.01)
        ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]["timeout-test"] = task

        with patch("ai.listeners.services.pubsub.memory_task.cleanup.get_pubsub_provider", return_value=mock_pubsub), \
             patch("framework.configs.settings.get_settings", return_value=mock_settings):
            # 在后台运行 cleanup
            cleanup_coro = cleanup_task_after_timeout("timeout-test", TASK_TYPE_GENERATE_LLM, "测试任务", 0.1)
            cleanup_task = asyncio.create_task(cleanup_coro)

            # 等待足够时间让 cleanup 完成（sleep 0.1 + wait_for 5 = 最多 5.2s，但我们只需验证 publish 被调用）
            await asyncio.sleep(0.5)

        # 验证：publish 被调用了
        mock_pubsub.publish.assert_called_once_with(
            CANCEL_ASYNCIO_TASK_TOPIC,
            {"task_id": "timeout-test", "task_type": TASK_TYPE_GENERATE_LLM},
        )

        # 清理：取消残留任务
        if not cleanup_task.done():
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_no_publish_when_task_already_done(self):
        """任务正常完成后，超时清理不应发布取消信号"""
        mock_pubsub, mock_settings = _make_mock_pubsub_and_settings()

        async def quick_task():
            return "done"

        task = asyncio.create_task(quick_task())
        await task
        ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]["quick-test"] = task

        with patch("ai.listeners.services.pubsub.memory_task.cleanup.get_pubsub_provider", return_value=mock_pubsub), \
             patch("framework.configs.settings.get_settings", return_value=mock_settings):
            cleanup_task = asyncio.create_task(
                cleanup_task_after_timeout("quick-test", TASK_TYPE_GENERATE_LLM, "测试任务", 0.1)
            )
            await asyncio.wait_for(cleanup_task, timeout=1.0)

        # 任务已完成后不应发布取消信号
        mock_pubsub.publish.assert_not_called()
        # 从活跃列表移除
        assert "quick-test" not in ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]

    @pytest.mark.asyncio
    async def test_cleanup_removes_itself_from_active_cleanup(self):
        """清理任务完成后应从 ACTIVE_CLEANUP_TASKS 中移除"""
        mock_pubsub, mock_settings = _make_mock_pubsub_and_settings()

        async def quick_task():
            return "done"

        task = asyncio.create_task(quick_task())
        await task
        ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]["self-cleanup"] = task

        with patch("ai.listeners.services.pubsub.memory_task.cleanup.get_pubsub_provider", return_value=mock_pubsub), \
             patch("framework.configs.settings.get_settings", return_value=mock_settings):
            cleanup_task = asyncio.create_task(
                cleanup_task_after_timeout("self-cleanup", TASK_TYPE_GENERATE_LLM, "测试任务", 0.1)
            )
            ACTIVE_CLEANUP_TASKS[TASK_TYPE_GENERATE_LLM]["self-cleanup"] = cleanup_task

            await asyncio.wait_for(cleanup_task, timeout=1.0)

        # 清理任务应从 ACTIVE_CLEANUP_TASKS 中移除
        assert "self-cleanup" not in ACTIVE_CLEANUP_TASKS.get(TASK_TYPE_GENERATE_LLM, {})

    @pytest.mark.asyncio
    async def test_dynamic_timeout_callable(self):
        """支持动态超时时间（从配置读取）"""
        mock_pubsub, mock_settings = _make_mock_pubsub_and_settings()

        async def quick_task():
            return "done"

        task = asyncio.create_task(quick_task())
        await task
        ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]["dynamic-test"] = task

        with patch("ai.listeners.services.pubsub.memory_task.cleanup.get_pubsub_provider", return_value=mock_pubsub), \
             patch("framework.configs.settings.get_settings", return_value=mock_settings):
            await asyncio.wait_for(
                cleanup_task_after_timeout("dynamic-test", TASK_TYPE_GENERATE_LLM, "测试任务", lambda: 0.1),
                timeout=1.0,
            )

        assert "dynamic-test" not in ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]
