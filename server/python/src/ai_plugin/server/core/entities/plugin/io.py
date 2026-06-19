from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_plugin.server.core.server.__base.request_reader import RequestReader

from ai_plugin.server.core.server.__base.response_writer import ResponseWriter


class PluginInStreamEvent(Enum):
    """插件输入流事件枚举"""

    Request = "request"  # 请求事件
    BackwardInvocationResponse = "backwards_response"  # 反向调用响应事件

    @classmethod
    def value_of(cls, v: str):
        """
        根据字符串值获取对应的枚举值

        Args:
            v: 字符串值

        Returns:
            对应的枚举值

        Raises:
            ValueError: 当值无效时抛出异常
        """
        for e in cls:
            if e.value == v:
                return e
        raise ValueError(f"Invalid value for PluginInStream.Event: {v}")


class PluginInStreamBase:
    """插件输入流基类"""

    def __init__(
        self,
        session_id: str,
        event: PluginInStreamEvent,
        data: dict,
        conversation_id: str | None = None,
        message_id: str | None = None,
        app_id: str | None = None,
        endpoint_id: str | None = None,
    ) -> None:
        """
        初始化插件输入流基类

        Args:
            session_id: 会话ID
            event: 插件流事件
            data: 数据字典
            conversation_id: 可选的对话ID
            message_id: 可选的消息ID
            app_id: 可选的应用ID
            endpoint_id: 可选的端点ID
        """
        self.session_id = session_id
        self.event = event
        self.data = data
        self.conversation_id = conversation_id
        self.message_id = message_id
        self.app_id = app_id
        self.endpoint_id = endpoint_id


class PluginInStream(PluginInStreamBase):
    """插件输入流类，包含读取器和写入器"""

    def __init__(
        self,
        session_id: str,
        event: PluginInStreamEvent,
        data: dict,
        reader: "RequestReader",
        writer: "ResponseWriter",
        conversation_id: str | None = None,
        message_id: str | None = None,
        app_id: str | None = None,
        endpoint_id: str | None = None,
    ):
        """
        初始化插件输入流

        Args:
            session_id: 会话ID
            event: 插件流事件
            data: 数据字典
            reader: 请求读取器
            writer: 响应写入器
            conversation_id: 可选的对话ID
            message_id: 可选的消息ID
            app_id: 可选的应用ID
            endpoint_id: 可选的端点ID
        """
        self.reader = reader
        self.writer = writer
        super().__init__(
            session_id, event, data, conversation_id, message_id, app_id, endpoint_id
        )
