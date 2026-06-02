from enum import Enum

from pydantic import BaseModel, Field


class Event(Enum):
    """流输出事件枚举"""

    LOG = "log"  # 日志事件
    ERROR = "error"  # 错误事件
    SESSION = "session"  # 会话事件
    HEARTBEAT = "heartbeat"  # 心跳事件


class StreamOutputMessage(BaseModel):
    """流输出消息模型"""

    event: Event  # 事件类型
    session_id: str | None = Field(default=None)  # 可选的会话ID
    data: dict | BaseModel | None = Field(default=None)  # 可选的数据内容
