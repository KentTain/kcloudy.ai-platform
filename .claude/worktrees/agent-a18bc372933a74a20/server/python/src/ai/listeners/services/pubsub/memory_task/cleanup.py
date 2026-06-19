"""超时清理任务"""

import asyncio
from collections.abc import Callable

from loguru import logger

from framework.pubsub import get_pubsub_provider
from ai.listeners.services.pubsub.constants import CANCEL_ASYNCIO_TASK_TOPIC
from ai.listeners.services.pubsub.memory_task.constants import ACTIVE_ASYNCIO_TASKS, ACTIVE_CLEANUP_TASKS

_logger = logger.bind(name=__name__)


async def cleanup_task_after_timeout(
    task_id: str,
    task_type: str,
    task_name: str,
    timeout_seconds: int | Callable[[], int],
) -> None:
    """在超时时间后清理异步任务"""
    try:
        timeout = timeout_seconds if isinstance(timeout_seconds, (int, float)) else timeout_seconds()

        await asyncio.sleep(timeout)

        if task_id in ACTIVE_ASYNCIO_TASKS[task_type]:
            task = ACTIVE_ASYNCIO_TASKS[task_type][task_id]
            if not task.done():
                from framework.configs.settings import get_settings
                settings = get_settings()
                pubsub = get_pubsub_provider(settings.messaging)
                await pubsub.publish(
                    CANCEL_ASYNCIO_TASK_TOPIC,
                    {"task_id": task_id, "task_type": task_type},
                )
                _logger.warning(f"{task_name}超时，取消执行: {task_id}")
                try:
                    await asyncio.wait_for(asyncio.shield(task), timeout=5)
                except (asyncio.CancelledError, TimeoutError):
                    pass

            ACTIVE_ASYNCIO_TASKS[task_type].pop(task_id, None)
            _logger.debug(f"已清理{task_name} {task_id} 的资源")

    except asyncio.CancelledError:
        _logger.debug(f"清理任务被取消（{task_name}已正常完成）: {task_id}")
        raise
    except Exception:
        _logger.exception(f"清理{task_name} {task_id} 资源时出错")
    finally:
        if task_type in ACTIVE_CLEANUP_TASKS and task_id in ACTIVE_CLEANUP_TASKS[task_type]:
            del ACTIVE_CLEANUP_TASKS[task_type][task_id]