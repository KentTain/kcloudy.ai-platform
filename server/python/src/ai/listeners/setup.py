"""Listeners 生命周期管理"""

from typing import TYPE_CHECKING

from loguru import logger

from ai.listeners.services.pubsub.constants import CANCEL_ASYNCIO_TASK_TOPIC
from ai.listeners.services.pubsub.memory_task.cancel_asyncio_task import (
    CancelAsyncioTaskHandler,
)
from ai.listeners.services.queue.install_task_consumer import (
    cleanup_install_task_consumer,
    setup_install_task_consumer,
)
from framework.pubsub import get_pubsub_provider

if TYPE_CHECKING:
    from framework.configs.settings import Settings

_logger = logger.bind(name=__name__)

_pubsub_provider = None
_cancel_task_handler = None


async def setup_listeners(settings: "Settings") -> None:
    """注册所有消息处理器"""
    global _pubsub_provider, _cancel_task_handler

    _pubsub_provider = get_pubsub_provider(settings.messaging)
    _cancel_task_handler = CancelAsyncioTaskHandler()

    await _pubsub_provider.subscribe(
        CANCEL_ASYNCIO_TASK_TOPIC, _cancel_task_handler.handle
    )

    # 注册安装任务消费者
    await setup_install_task_consumer(settings)

    _logger.info("Listeners 注册完成")


async def cleanup_listeners() -> None:
    """取消所有消息处理器订阅"""
    if _pubsub_provider:
        await _pubsub_provider.unsubscribe(CANCEL_ASYNCIO_TASK_TOPIC)

    # 清理安装任务消费者
    await cleanup_install_task_consumer()

    _logger.info("Listeners 清理完成")
