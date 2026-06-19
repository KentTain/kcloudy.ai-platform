"""Listeners 生命周期管理"""

from typing import TYPE_CHECKING

from loguru import logger

from framework.pubsub import get_pubsub_provider
from framework.queue import get_queue_provider
from demo.listeners.services.pubsub.constants import HEARTBEAT_TOPIC
from demo.listeners.services.pubsub.heartbeat_handler import HeartbeatHandler
from demo.listeners.services.queue.constants import DATASET_NOTIFY_QUEUE
from demo.listeners.services.queue.dataset_notify_handler import (
    DatasetNotifyHandler,
)

if TYPE_CHECKING:
    from framework.configs.settings import Settings

_logger = logger.bind(name=__name__)

_pubsub_provider = None
_queue_provider = None
_heartbeat_handler = None
_dataset_notify_handler = None


async def setup_listeners(settings: "Settings") -> None:
    """注册所有消息处理器"""
    global _pubsub_provider, _queue_provider
    global _heartbeat_handler, _dataset_notify_handler

    _pubsub_provider = get_pubsub_provider(settings.messaging)
    _queue_provider = get_queue_provider(settings.messaging)

    _heartbeat_handler = HeartbeatHandler()
    _dataset_notify_handler = DatasetNotifyHandler()

    await _pubsub_provider.subscribe(HEARTBEAT_TOPIC, _heartbeat_handler.handle)

    await _queue_provider.create_consumer_group(
        DATASET_NOTIFY_QUEUE,
        f"{DATASET_NOTIFY_QUEUE}:group",
    )

    _logger.info("Listeners 注册完成")


async def cleanup_listeners() -> None:
    """取消所有消息处理器订阅"""
    if _pubsub_provider:
        await _pubsub_provider.unsubscribe(HEARTBEAT_TOPIC)
    _logger.info("Listeners 清理完成")
