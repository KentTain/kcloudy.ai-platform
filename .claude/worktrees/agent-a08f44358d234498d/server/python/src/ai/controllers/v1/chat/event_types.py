"""SSE 事件类型定义

AI SDK UIMessageChunk 标准事件类型。
"""

from enum import Enum


class EventType(str, Enum):
    """SSE 事件类型（AI SDK UIMessageChunk 标准）"""

    START = "start"
    TEXT_START = "text-start"
    TEXT_DELTA = "text-delta"
    TEXT_END = "text-end"
    TOOL_CALL = "tool-call"
    TOOL_RESULT = "tool-result"
    FINISH = "finish"
    ERROR = "error"
