"""内存任务辅助函数"""

import asyncio

from loguru import logger

from ai.listeners.services.pubsub.constants import CANCEL_ASYNCIO_TASK_TOPIC
from ai.listeners.services.pubsub.memory_task.constants import (
    ACTIVE_ASYNCIO_TASKS,
    ACTIVE_CLEANUP_TASKS,
)
from ai.models.enums import MessageStatus
from framework.database.core.engine import get_session
from framework.pubsub import get_pubsub_provider

_logger = logger.bind(name=__name__)


async def stop_task_by_id(
    task_id: str,
    task_type: str,
    task_name: str = "任务",
    message_id: str | None = None,
) -> dict:
    """停止任务：先在本地查找并取消，如未找到则广播取消请求"""
    local_cancelled = False
    message = f"未在本地实例找到对应{task_name}，已广播取消请求到所有实例"

    if task_id in ACTIVE_ASYNCIO_TASKS[task_type]:
        task = ACTIVE_ASYNCIO_TASKS[task_type][task_id]
        if not task.done():
            task.cancel()
            local_cancelled = True
            message = f"已在本地取消{task_name}"
            _logger.info(f"在本地取消{task_name}: {task_id}, task_type={task_type}")
            # 本地取消成功后更新消息状态
            if message_id:
                await stop_message_by_id(message_id)
        else:
            message = f"{task_name}已完成，无需取消"
            _logger.info(f"{task_name} {task_id} 已完成，无需取消, task_type={task_type}")

    if not local_cancelled:
        from framework.configs.settings import get_settings
        settings = get_settings()
        pubsub = get_pubsub_provider(settings.messaging)
        payload = {"task_id": task_id, "task_type": task_type}
        if message_id:
            payload["message_id"] = message_id
        await pubsub.publish(CANCEL_ASYNCIO_TASK_TOPIC, payload)
        _logger.info(f"广播{task_name}取消请求: {task_id}, task_type={task_type}")

    return {"message": message, "local_cancelled": local_cancelled}


async def cleanup_task_resources(
    task_id: str,
    task_type: str,
    task_name: str = "任务",
) -> None:
    """清理任务执行完成后的资源"""
    ACTIVE_ASYNCIO_TASKS[task_type].pop(task_id, None)

    if task_type in ACTIVE_CLEANUP_TASKS and task_id in ACTIVE_CLEANUP_TASKS[task_type]:
        active_cleanup_task = ACTIVE_CLEANUP_TASKS[task_type][task_id]
        if not active_cleanup_task.done():
            active_cleanup_task.cancel()
            _logger.debug(f"主动取消{task_name}清理任务: {task_id}")
            try:
                await active_cleanup_task
            except asyncio.CancelledError:
                pass
            except Exception:
                _logger.exception(f"取消{task_name}清理任务 {task_id} 时出错")


async def stop_message_by_id(message_id: str) -> bool:
    """将指定消息的状态更新为 stopped"""
    from ai.models.message import Message

    try:
        async with get_session() as session:
            msg = await session.get(Message, message_id)
            if msg is not None and msg.status != MessageStatus.STOPPED:
                msg.status = MessageStatus.STOPPED
                await session.flush()
                await session.commit()
                _logger.info(f"消息状态已更新为 stopped: {message_id}")
                return True
            return False
    except Exception:
        _logger.exception(f"更新消息状态为 stopped 失败: {message_id}")
        return False
