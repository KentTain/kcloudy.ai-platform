"""
发布订阅接口定义

使用 Python Protocol 定义统一的发布订阅接口。
"""

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PubSubProvider(Protocol):
    """
    发布订阅提供者协议

    定义统一的发布订阅接口，支持 Redis PubSub 等实现。
    """

    async def publish(self, topic: str, message: dict[str, Any]) -> bool:
        """
        发布消息

        Args:
            topic: 主题名称
            message: 消息体

        Returns:
            bool: 是否成功
        """
        ...

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[str, dict[str, Any]], None]
    ) -> bool:
        """
        订阅主题

        Args:
            topic: 主题名称
            handler: 消息处理函数

        Returns:
            bool: 是否成功
        """
        ...

    async def unsubscribe(self, topic: str) -> bool:
        """
        取消订阅

        Args:
            topic: 主题名称

        Returns:
            bool: 是否成功
        """
        ...

    async def get_subscribers(self, topic: str) -> int:
        """
        获取主题订阅者数量

        Args:
            topic: 主题名称

        Returns:
            int: 订阅者数量
        """
        ...

    async def pattern_subscribe(
        self,
        pattern: str,
        handler: Callable[[str, dict[str, Any]], None]
    ) -> bool:
        """
        模式订阅

        Args:
            pattern: 主题模式（如 "news:*"）
            handler: 消息处理函数

        Returns:
            bool: 是否成功
        """
        ...
