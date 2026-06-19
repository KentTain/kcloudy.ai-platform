"""
队列接口定义

使用 Python Protocol 定义统一的队列接口。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@dataclass
class Message:
    """消息对象"""

    id: str
    """消息 ID"""

    body: dict[str, Any]
    """消息体"""

    queue: str
    """队列名称"""

    timestamp: datetime = field(default_factory=datetime.now)
    """消息时间戳"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """元数据"""


@runtime_checkable
class QueueProvider(Protocol):
    """
    队列提供者协议

    定义统一的消息队列接口，支持 Redis Stream 等实现。
    """

    async def enqueue(
        self,
        queue: str,
        message: dict[str, Any],
        delay: int | None = None
    ) -> str:
        """
        消息入队

        Args:
            queue: 队列名称
            message: 消息体
            delay: 延迟时间（秒）

        Returns:
            str: 消息 ID
        """
        ...

    async def dequeue(
        self,
        queue: str,
        count: int = 1,
        timeout: int = 0
    ) -> list[Message]:
        """
        消息出队

        Args:
            queue: 队列名称
            count: 最大消息数量
            timeout: 阻塞等待超时（秒）

        Returns:
            list[Message]: 消息列表
        """
        ...

    async def ack(self, queue: str, message_id: str) -> bool:
        """
        确认消息

        Args:
            queue: 队列名称
            message_id: 消息 ID

        Returns:
            bool: 是否成功
        """
        ...

    async def nack(self, queue: str, message_id: str) -> bool:
        """
        拒绝消息（重新入队）

        Args:
            queue: 队列名称
            message_id: 消息 ID

        Returns:
            bool: 是否成功
        """
        ...

    async def get_queue_length(self, queue: str) -> int:
        """
        获取队列长度

        Args:
            queue: 队列名称

        Returns:
            int: 队列长度
        """
        ...

    async def purge(self, queue: str) -> bool:
        """
        清空队列

        Args:
            queue: 队列名称

        Returns:
            bool: 是否成功
        """
        ...

    async def create_consumer_group(
        self,
        queue: str,
        group: str,
        start_id: str = "0"
    ) -> bool:
        """
        创建消费者组

        Args:
            queue: 队列名称
            group: 消费者组名称
            start_id: 起始消息 ID

        Returns:
            bool: 是否成功
        """
        ...
