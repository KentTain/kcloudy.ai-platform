"""
核心接口模块

使用 Python Protocol 定义 Storage、Queue、PubSub、Lock 接口。
"""

from framework.core.constants import (
    DEFAULT_SORT,
    DEFAULT_TREE_ROOT_ID,
    TREE_SORTS_LENGTH,
    TREE_SORTS_PADSTR,
)
from framework.core.lock import Lock, LockProvider
from framework.core.pubsub import PubSubProvider
from framework.core.queue import Message, QueueProvider
from framework.core.storage import StorageProvider

__all__ = [
    "StorageProvider",
    "QueueProvider",
    "Message",
    "PubSubProvider",
    "LockProvider",
    "Lock",
    "DEFAULT_SORT",
    "TREE_SORTS_LENGTH",
    "TREE_SORTS_PADSTR",
    "DEFAULT_TREE_ROOT_ID",
]
