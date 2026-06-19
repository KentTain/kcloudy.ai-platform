"""取消异步任务处理器"""

from typing import Any, override

from loguru import logger

from ai.listeners.services.pubsub.constants import CANCEL_ASYNCIO_TASK_TOPIC
from ai.listeners.services.pubsub.memory_task.constants import ACTIVE_ASYNCIO_TASKS
from ai.listeners.services.pubsub.memory_task.helpers import stop_message_by_id
from framework.pubsub.handler import SingleTopicHandler

_logger = logger.bind(name=__name__)


class CancelAsyncioTaskHandler(SingleTopicHandler):
    """接收其他节点的取消异步任务请求，取消本节点的 asyncio 任务"""

    topic: str = CANCEL_ASYNCIO_TASK_TOPIC

    @override
    async def handle(self, topic: str, message: dict[str, Any]) -> None:
        task_id = message.get("task_id")
        task_type = message.get("task_type")
        message_id = message.get("message_id")

        if not task_id or not task_type:
            _logger.error(f"取消异步任务消息缺少 task_id 或 task_type: {message}")
            return

        try:
            if task_type in ACTIVE_ASYNCIO_TASKS and task_id in ACTIVE_ASYNCIO_TASKS[task_type]:
                task = ACTIVE_ASYNCIO_TASKS[task_type][task_id]
                if not task.done():
                    task.cancel()
                    _logger.info(f"成功取消异步任务: task_type={task_type}, task_id={task_id}")
                else:
                    _logger.info(f"异步任务已完成，无需取消: task_type={task_type}, task_id={task_id}")

            # 更新对应消息状态为 stopped
            if message_id:
                await stop_message_by_id(message_id)
        except Exception:
            _logger.exception(f"取消异步任务异常: task_type={task_type}, task_id={task_id}")
