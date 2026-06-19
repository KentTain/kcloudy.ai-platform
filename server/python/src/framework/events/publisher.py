"""
事件发布器

提供领域事件的发布能力，基于 Redis Stream 实现。
"""

from __future__ import annotations

import logging
from typing import Any

from framework.cache.redis_util import RedisUtil
from framework.events.base import DomainEvent

_logger = logging.getLogger(__name__)


class EventPublisher:
    """
    事件发布器

    基于 Redis Stream 实现事件发布。
    支持异步发布，确保消息可靠性。

    Usage:
        publisher = EventPublisher()
        await publisher.publish(ModuleAssigned(tenant_id="xxx", module_id="yyy"))
    """

    # Stream 名称前缀（可用于租户隔离）
    _prefix: str = ""

    def __init__(self, prefix: str = ""):
        """
        初始化事件发布器

        Args:
            prefix: Stream 名称前缀（可选，用于租户隔离）
        """
        self._prefix = prefix

    def _get_stream_name(self, event: DomainEvent) -> str:
        """
        获取完整的 Stream 名称

        Args:
            event: 领域事件

        Returns:
            完整的 Stream 名称
        """
        base_name = event.get_stream_name()
        if self._prefix:
            return f"{self._prefix}:{base_name}"
        return base_name

    async def publish(self, event: DomainEvent) -> str:
        """
        发布单个事件

        Args:
            event: 领域事件

        Returns:
            str: 消息 ID

        Raises:
            RuntimeError: Redis 未初始化
        """
        stream_name = self._get_stream_name(event)
        event_data = event.to_dict()

        # 构建 Stream 消息字段
        fields: dict[str, Any] = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "data": event.to_json(),
        }

        # 发布到 Redis Stream
        message_id = await RedisUtil.xadd(stream_name, fields)

        _logger.info(
            f"发布事件: {event.event_type} -> {stream_name}, "
            f"event_id={event.event_id}, message_id={message_id}"
        )

        return message_id

    async def publish_batch(self, events: list[DomainEvent]) -> list[str]:
        """
        批量发布事件

        Args:
            events: 领域事件列表

        Returns:
            list[str]: 消息 ID 列表
        """
        message_ids = []
        for event in events:
            message_id = await self.publish(event)
            message_ids.append(message_id)
        return message_ids

    async def publish_with_retry(
        self,
        event: DomainEvent,
        max_retries: int = 3,
        retry_delay: float = 0.1,
    ) -> str:
        """
        带重试的事件发布

        Args:
            event: 领域事件
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）

        Returns:
            str: 消息 ID

        Raises:
            RuntimeError: 重试次数用尽仍失败
        """
        import asyncio

        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                return await self.publish(event)
            except Exception as e:
                last_error = e
                _logger.warning(
                    f"事件发布失败，尝试重试 ({attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)

        raise RuntimeError(
            f"事件发布失败，重试 {max_retries} 次后仍失败: {last_error}"
        )


# 全局单例实例
# 注意：需要在 Redis 初始化后使用
event_publisher = EventPublisher()


def get_event_publisher() -> EventPublisher:
    """
    获取事件发布器实例

    Returns:
        EventPublisher: 全局事件发布器实例
    """
    return event_publisher
