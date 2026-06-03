"""内存任务管控单元测试"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.listeners.services.pubsub.memory_task.constants import (
    ACTIVE_ASYNCIO_TASKS,
    ACTIVE_CLEANUP_TASKS,
    TASK_TYPE_GENERATE_LLM,
)
from ai.listeners.services.pubsub.memory_task.cancel_asyncio_task import (
    CancelAsyncioTaskHandler,
)
from ai.listeners.services.pubsub.constants import CANCEL_ASYNCIO_TASK_TOPIC


@pytest.fixture(autouse=True)
def cleanup_active_tasks():
    """每个测试后清理活跃任务字典"""
    yield
    ACTIVE_ASYNCIO_TASKS.clear()
    ACTIVE_CLEANUP_TASKS.clear()


class TestConstants:
    def test_task_type_generate_llm(self):
        assert TASK_TYPE_GENERATE_LLM == "generate:llm"

    def test_active_tasks_is_defaultdict(self):
        from collections import defaultdict
        assert isinstance(ACTIVE_ASYNCIO_TASKS, defaultdict)

    def test_active_cleanup_tasks_is_defaultdict(self):
        from collections import defaultdict
        assert isinstance(ACTIVE_CLEANUP_TASKS, defaultdict)


class TestCancelAsyncioTaskHandler:
    def test_topic(self):
        handler = CancelAsyncioTaskHandler()
        assert handler.topic == CANCEL_ASYNCIO_TASK_TOPIC

    @pytest.mark.asyncio
    async def test_handle_missing_task_id(self):
        handler = CancelAsyncioTaskHandler()
        # 不应抛出异常
        await handler.handle(CANCEL_ASYNCIO_TASK_TOPIC, {"task_type": TASK_TYPE_GENERATE_LLM})

    @pytest.mark.asyncio
    async def test_handle_missing_task_type(self):
        handler = CancelAsyncioTaskHandler()
        await handler.handle(CANCEL_ASYNCIO_TASK_TOPIC, {"task_id": "test-123"})

    @pytest.mark.asyncio
    async def test_handle_cancels_active_task(self):
        handler = CancelAsyncioTaskHandler()

        async def dummy_coro():
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                return "cancelled"

        task = asyncio.create_task(dummy_coro())
        # 给 asyncio 一点时间让任务开始运行
        await asyncio.sleep(0.01)
        ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]["test-123"] = task

        await handler.handle(
            CANCEL_ASYNCIO_TASK_TOPIC,
            {"task_id": "test-123", "task_type": TASK_TYPE_GENERATE_LLM},
        )

        # cancel() 已调用，任务会最终完成（通过 CancelledError）
        try:
            await asyncio.wait_for(task, timeout=0.5)
        except (asyncio.CancelledError, TimeoutError):
            pass
        assert task.done()

    @pytest.mark.asyncio
    async def test_handle_task_already_done(self):
        handler = CancelAsyncioTaskHandler()

        async def quick_coro():
            return "done"

        task = asyncio.create_task(quick_coro())
        await task  # 等待完成

        ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]["test-456"] = task

        # 不应抛出异常，任务已完成
        await handler.handle(
            CANCEL_ASYNCIO_TASK_TOPIC,
            {"task_id": "test-456", "task_type": TASK_TYPE_GENERATE_LLM},
        )

    @pytest.mark.asyncio
    async def test_handle_unknown_task_type(self):
        handler = CancelAsyncioTaskHandler()
        # 未知任务类型，不应抛出异常
        await handler.handle(
            CANCEL_ASYNCIO_TASK_TOPIC,
            {"task_id": "test-789", "task_type": "unknown:type"},
        )


class TestStopTaskById:
    @pytest.mark.asyncio
    async def test_cancel_local_task(self):
        from ai.listeners.services.pubsub.memory_task.helpers import stop_task_by_id

        async def dummy_coro():
            await asyncio.sleep(100)

        task = asyncio.create_task(dummy_coro())
        ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]["test-local"] = task

        result = await stop_task_by_id("test-local", TASK_TYPE_GENERATE_LLM, "测试任务")

        assert result["local_cancelled"] is True
        assert "已在本地取消" in result["message"]

    @pytest.mark.asyncio
    async def test_broadcast_when_not_local(self):
        from ai.listeners.services.pubsub.memory_task.helpers import stop_task_by_id

        mock_pubsub = AsyncMock()
        mock_pubsub.publish = AsyncMock(return_value=True)
        mock_settings = MagicMock()
        mock_settings.messaging = MagicMock()

        # helpers.py 使用 module-level import: from framework.pubsub import get_pubsub_provider
        # 所以必须 patch helpers 模块本地的引用
        with patch(
            "ai.listeners.services.pubsub.memory_task.helpers.get_pubsub_provider",
            return_value=mock_pubsub,
        ), patch(
            "framework.configs.settings.get_settings",
            return_value=mock_settings,
        ):
            result = await stop_task_by_id("nonexistent", TASK_TYPE_GENERATE_LLM, "测试任务")

        assert result["local_cancelled"] is False
        assert "广播" in result["message"]
        mock_pubsub.publish.assert_called_once()


class TestCleanupTaskResources:
    @pytest.mark.asyncio
    async def test_removes_from_active_tasks(self):
        from ai.listeners.services.pubsub.memory_task.helpers import cleanup_task_resources

        async def dummy_coro():
            await asyncio.sleep(100)

        task = asyncio.create_task(dummy_coro())
        ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]["test-cleanup"] = task
        task.cancel()

        await cleanup_task_resources("test-cleanup", TASK_TYPE_GENERATE_LLM, "测试任务")

        assert "test-cleanup" not in ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM]