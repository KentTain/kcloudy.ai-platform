"""
队列工厂

根据配置返回对应的队列实现。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framework.configs.settings import MessagingSettings
    from framework.core.queue import QueueProvider


def get_queue_provider(config: "MessagingSettings") -> "QueueProvider":
    """
    获取队列提供者

    Args:
        config: 消息队列配置

    Returns:
        QueueProvider: 队列提供者实例

    Raises:
        ValueError: 不支持的队列类型
    """
    queue_type = config.queue.use.lower()

    match queue_type:
        case "redis":
            from framework.queue.impl.redis import RedisQueue
            redis_config = config.connections.get("redis", {})
            return RedisQueue(redis_config)
        case _:
            raise ValueError(f"不支持的队列类型: {queue_type}")
