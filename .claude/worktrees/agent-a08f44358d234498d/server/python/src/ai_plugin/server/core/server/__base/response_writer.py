from abc import ABC, abstractmethod

from pydantic import BaseModel

from ai_plugin.server.core.entities.message import SessionMessage
from ai_plugin.server.core.server.__base.writer_entities import (
    Event,
    StreamOutputMessage,
)


class ResponseWriter(ABC):
    """
    单个插件请求的响应写入器抽象基类
    """

    @abstractmethod
    def write(self, data: str):
        """
        将数据写入响应流

        Args:
            data: 要写入的字符串数据

        子类必须实现此方法来定义具体的写入行为
        """

    @abstractmethod
    def done(self):
        """
        完成当前轮次的处理

        标记当前请求处理完成，子类可以在此方法中执行清理操作
        """

    def put(
        self,
        event: Event,
        session_id: str | None = None,
        data: dict | BaseModel | None = None,
    ):
        """
        将输出序列化并发送给守护进程

        Args:
            event: 事件类型
            session_id: 可选的会话ID
            data: 可选的数据内容（字典或BaseModel）
        """
        # 如果数据是BaseModel实例，转换为字典
        if isinstance(data, BaseModel):
            data = data.model_dump()

        # 创建流输出消息并写入
        self.write(
            StreamOutputMessage(
                event=event, session_id=session_id, data=data
            ).model_dump_json()
        )
        self.write("\n\n")

    def error(
        self, session_id: str | None = None, data: dict | BaseModel | None = None
    ):
        """
        发送错误事件

        Args:
            session_id: 可选的会话ID
            data: 可选的错误数据

        Returns:
            put方法的返回值
        """
        return self.put(Event.ERROR, session_id, data)

    def log(self, data: dict | None = None):
        """
        发送日志事件

        Args:
            data: 可选的日志数据

        Returns:
            put方法的返回值
        """
        return self.put(Event.LOG, None, data)

    def heartbeat(self):
        """
        发送心跳事件

        Returns:
            put方法的返回值
        """
        return self.put(Event.HEARTBEAT, None, {})

    def session_message(
        self, session_id: str | None = None, data: dict | BaseModel | None = None
    ):
        """
        发送会话消息事件

        Args:
            session_id: 可选的会话ID
            data: 可选的消息数据

        Returns:
            put方法的返回值
        """
        return self.put(Event.SESSION, session_id, data)

    def session_message_text(
        self, session_id: str | None = None, data: dict | BaseModel | None = None
    ) -> str:
        """
        生成会话消息的文本表示

        Args:
            session_id: 可选的会话ID
            data: 可选的消息数据

        Returns:
            格式化的会话消息JSON字符串
        """
        # 如果数据是BaseModel实例，转换为字典
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return (
            StreamOutputMessage(
                event=Event.SESSION, session_id=session_id, data=data
            ).model_dump_json()
            + "\n\n"
        )

    def stream_object(self, data: dict | BaseModel) -> SessionMessage:
        """
        创建流式数据对象

        Args:
            data: 要流式传输的数据

        Returns:
            SessionMessage: 流式消息对象
        """
        # 如果数据是BaseModel实例，转换为字典
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return SessionMessage(type=SessionMessage.Type.STREAM, data=data)

    def stream_end_object(self) -> SessionMessage:
        """
        创建流式结束对象

        Returns:
            SessionMessage: 流式结束消息对象
        """
        return SessionMessage(type=SessionMessage.Type.END, data={})

    def stream_error_object(self, data: dict | BaseModel) -> SessionMessage:
        """
        创建流式错误对象

        Args:
            data: 错误数据

        Returns:
            SessionMessage: 流式错误消息对象
        """
        # 如果数据是BaseModel实例，转换为字典
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return SessionMessage(type=SessionMessage.Type.ERROR, data=data)

    def stream_invoke_object(self, data: dict | BaseModel) -> SessionMessage:
        """
        创建流式调用对象

        Args:
            data: 调用数据

        Returns:
            SessionMessage: 流式调用消息对象
        """
        # 如果数据是BaseModel实例，转换为字典
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return SessionMessage(type=SessionMessage.Type.INVOKE, data=data)
