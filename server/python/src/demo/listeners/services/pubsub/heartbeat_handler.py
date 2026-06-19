"""心跳消息处理器"""

from typing import Any

from loguru import logger

from demo.listeners.services.pubsub.constants import HEARTBEAT_TOPIC
from framework.pubsub.handler import SingleTopicHandler

_logger = logger.bind(name=__name__)


class HeartbeatHandler(SingleTopicHandler):
    """监听 demo:heartbeat 主题，记录心跳消息"""

    topic: str = HEARTBEAT_TOPIC

    async def handle(self, topic: str, message: dict[str, Any]) -> None:
        _logger.info(f"{topic} => 收到心跳消息: {message}")
