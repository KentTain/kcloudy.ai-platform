"""
核心接口模块

使用 Python Protocol 定义 Storage、Queue、PubSub、Lock 接口。
"""

from framework.core.storage import StorageProvider
from framework.core.queue import QueueProvider, Message
from framework.core.pubsub import PubSubProvider
from framework.core.lock import LockProvider, Lock

__all__ = [
    "StorageProvider",
    "QueueProvider",
    "Message",
    "PubSubProvider",
    "LockProvider",
    "Lock",
]
