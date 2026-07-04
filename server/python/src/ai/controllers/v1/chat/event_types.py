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

    # 思考过程事件
    THINKING_START = "thinking-start"    # 思考块开始
    THINKING_DELTA = "thinking-delta"    # 思考内容增量
    THINKING_END = "thinking-end"        # 思考块结束
