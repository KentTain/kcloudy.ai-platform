"""
队列模块

提供 Redis Stream 等消息队列实现。
"""

from framework.queue.factory import get_queue_provider
from framework.queue.handler import QueueMessageHandler, SingleQueueHandler

__all__ = [
    "get_queue_provider",
    "QueueMessageHandler",
    "SingleQueueHandler",
]
