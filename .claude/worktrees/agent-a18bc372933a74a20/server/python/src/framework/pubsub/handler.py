"""
发布订阅消息处理器基类
"""

from abc import ABC, abstractmethod
from typing import Any


class TopicMessageHandler(ABC):
    """
    主题消息处理器基类

    定义消息处理的标准接口。
    """

    @abstractmethod
    async def handle(self, topic: str, message: dict[str, Any]) -> None:
        """
        处理消息

        Args:
            topic: 主题名称
            message: 消息体
        """
        pass

    def get_topics(self) -> list[str]:
        """
        获取订阅的主题列表

        Returns:
            list[str]: 主题列表
        """
        return []


class SingleTopicHandler(TopicMessageHandler):
    """
    单主题处理器

    简化单主题处理的基类。
    """

    topic: str = ""
    """订阅的主题名称"""

    def get_topics(self) -> list[str]:
        if not self.topic:
            raise ValueError(f"{self.__class__.__name__}.topic 未设置")
        return [self.topic]


class MultiTopicHandler(TopicMessageHandler):
    """
    多主题处理器

    支持订阅多个主题的基类。
    """

    topics: list[str] = []
    """订阅的主题列表"""

    def get_topics(self) -> list[str]:
        if not self.topics:
            raise ValueError(f"{self.__class__.__name__}.topics 未设置")
        return self.topics
