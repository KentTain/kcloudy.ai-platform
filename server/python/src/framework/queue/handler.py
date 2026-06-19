"""
队列消息处理器基类
"""

from abc import ABC, abstractmethod

from framework.core.queue import Message


class QueueMessageHandler(ABC):
    """
    队列消息处理器基类

    定义消息处理的标准接口。
    """

    @abstractmethod
    async def handle(self, queue: str, messages: list[Message]) -> None:
        """
        处理队列消息

        Args:
            queue: 队列名称
            messages: 消息列表
        """
        pass

    def get_queue_name(self) -> str:
        """
        获取队列名称

        Returns:
            str: 队列名称
        """
        return getattr(self, "queue", "")

    def get_batch_size(self) -> int:
        """
        获取批量处理大小

        Returns:
            int: 批量大小
        """
        return getattr(self, "batch_size", 10)


class SingleQueueHandler(QueueMessageHandler):
    """
    单队列处理器

    简化单队列处理的基类。
    """

    queue: str = ""
    """队列名称"""

    batch_size: int = 10
    """批量处理大小"""

    def get_queue_name(self) -> str:
        if not self.queue:
            raise ValueError(f"{self.__class__.__name__}.queue 未设置")
        return self.queue

    def get_batch_size(self) -> int:
        return self.batch_size
