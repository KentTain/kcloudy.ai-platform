"""数据集通知队列处理器"""

from typing import Any

from loguru import logger

from framework.core.queue import Message
from framework.queue.handler import SingleQueueHandler
from demo.listeners.services.queue.constants import DATASET_NOTIFY_QUEUE

_logger = logger.bind(name=__name__)


class DatasetNotifyHandler(SingleQueueHandler):
    """消费 demo:dataset:notify 队列，处理数据集通知"""

    queue: str = DATASET_NOTIFY_QUEUE
    batch_size: int = 10

    async def handle(self, queue: str, messages: list[Message]) -> None:
        for message in messages:
            body = message.body
            dataset_id = body.get("dataset_id")
            if not dataset_id:
                _logger.warning(
                    f"{queue} => 消息缺少 dataset_id 字段，跳过: {body}"
                )
                continue
            _logger.info(f"{queue} => 收到数据集通知: {body}")
