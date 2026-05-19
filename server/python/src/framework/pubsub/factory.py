"""
发布订阅工厂

根据配置返回对应的发布订阅实现。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framework.config.settings import MessagingSettings
    from framework.core.pubsub import PubSubProvider


def get_pubsub_provider(config: "MessagingSettings") -> "PubSubProvider":
    """
    获取发布订阅提供者

    Args:
        config: 消息队列配置

    Returns:
        PubSubProvider: 发布订阅提供者实例

    Raises:
        ValueError: 不支持的类型
    """
    pubsub_type = config.pubsub.use.lower()

    match pubsub_type:
        case "redis":
            from framework.pubsub.impl.redis import RedisPubSub
            redis_config = config.connections.get("redis", {})
            return RedisPubSub(redis_config)
        case _:
            raise ValueError(f"不支持的发布订阅类型: {pubsub_type}")
