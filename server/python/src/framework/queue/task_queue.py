"""
租户感知的任务队列

自动携带租户上下文。
"""

from typing import Any

from loguru import logger

from framework.cache.tenant_redis_util import TenantRedisUtil
from framework.queue.task_message import TaskMessage

_logger = logger.bind(name=__name__)

# 默认队列名称
DEFAULT_QUEUE = "default"


class TenantTaskQueue:
    """
    租户感知的任务队列

    场景：任务入队自动携带租户 ID
    WHEN 在租户上下文为 `tenant_001` 时入队任务
    THEN 任务消息自动包含 `tenant_id: "tenant_001"`
    """

    @staticmethod
    async def enqueue(
        task_type: str,
        payload: dict[str, Any],
        queue_name: str = DEFAULT_QUEUE,
    ) -> str:
        """
        入队任务

        Args:
            task_type: 任务类型
            payload: 任务负载
            queue_name: 队列名称

        Returns:
            str: 任务 ID
        """
        message = TaskMessage(task_type=task_type, payload=payload)

        # 入队（自动添加租户前缀）
        await TenantRedisUtil.xadd(queue_name, message.to_dict())

        _logger.debug(
            f"任务入队: {message.task_id}, type={task_type}, tenant={message.tenant_id}"
        )
        return message.task_id

    @staticmethod
    async def dequeue(
        queue_name: str = DEFAULT_QUEUE,
        count: int = 1,
        block: int | None = None,
    ) -> list[TaskMessage]:
        """
        出队任务

        Args:
            queue_name: 队列名称
            count: 获取数量
            block: 阻塞时间（毫秒）

        Returns:
            list[TaskMessage]: 任务消息列表
        """
        messages = await TenantRedisUtil.xread([queue_name], count=count, block=block)

        tasks = []
        for stream_name, stream_messages in messages:
            for msg_id, msg_data in stream_messages:
                task = TaskMessage.from_dict(msg_data)
                tasks.append(task)

        return tasks


# 便捷函数
async def enqueue_task(
    task_type: str, payload: dict[str, Any], queue_name: str = DEFAULT_QUEUE
) -> str:
    """入队任务"""
    return await TenantTaskQueue.enqueue(task_type, payload, queue_name)
