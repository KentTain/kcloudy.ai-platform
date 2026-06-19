"""UIMessageChunkCallbackHandler - 将 LangChain 事件转换为 AI SDK 格式

继承 LangChain AsyncCallbackHandler，拦截工具调用事件和 LLM 流式输出事件，
转换为 AI SDK UIMessageChunk 标准格式发送到事件队列。

事件映射：
- on_llm_new_token -> text-delta (LLM 流式输出)
- on_tool_start -> tool-call (工具调用开始)
- on_tool_end -> tool-result (工具调用结束)
- on_tool_error -> tool-result (工具调用错误)
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from langchain_core.callbacks import AsyncCallbackHandler
from loguru import logger

from ai.controllers.v1.chat.event_types import EventType

_logger = logger.bind(name=__name__)


class UIMessageChunkCallbackHandler(AsyncCallbackHandler):
    """将 LangChain 事件转换为 AI SDK UIMessageChunk 格式

    职责边界：
    - 监听 LangChain LLM 流式输出事件（on_llm_new_token）
    - 监听 LangChain 工具调用事件（on_tool_start, on_tool_end）
    - 转换为 AI SDK 标准格式（text-delta, tool-call, tool-result）
    - 发送到事件队列供 SSE 流消费

    架构设计：
    所有事件（包括文本流和工具调用）统一通过 CallbackHandler 处理，
    符合规格定义的单一路径架构：
    agent.astream_events() → UIMessageChunkCallbackHandler → event_queue

    不负责：
    - usage 统计（保留在 run_llm_task 中）
    - 数据库持久化
    """

    def __init__(self, event_queue: asyncio.Queue, message_id: str = "") -> None:
        """初始化回调处理器

        Args:
            event_queue: 事件队列，用于发送 SSE 事件
            message_id: 消息 ID，用于生成 text-delta 事件的 id
        """
        super().__init__()
        self.event_queue = event_queue
        self._tool_call_ids: dict[str, str] = {}  # run_id -> tool_call_id 映射
        self.message_id = message_id
        self.full_content = ""  # 累积文本内容

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """工具调用开始时触发

        发送 tool-call 事件到队列，格式：
        {
            "type": "tool-call",
            "toolCallId": "<run_id>",
            "toolName": "<tool_name>",
            "args": <input_args>
        }

        Args:
            serialized: 序列化的工具信息，包含工具名称
            input_str: 输入字符串（已废弃，使用 inputs）
            run_id: 当前运行 ID，用作 toolCallId
            parent_run_id: 父运行 ID
            tags: 标签列表
            metadata: 元数据
            inputs: 工具输入参数
            **kwargs: 其他参数
        """
        try:
            # 提取工具名称（按优先级尝试多个来源）
            tool_name = serialized.get("name")
            if not tool_name:
                tool_name = kwargs.get("name")
            if not tool_name and metadata:
                tool_name = metadata.get("tool_name")
            if not tool_name:
                tool_name = "unknown_tool"

            # 生成 tool_call_id（使用 run_id）
            tool_call_id = str(run_id)
            self._tool_call_ids[tool_call_id] = tool_name

            # 准备参数
            args = inputs if inputs else ({"input": input_str} if input_str else {})

            event = {
                "type": EventType.TOOL_CALL,
                "toolCallId": tool_call_id,
                "toolName": tool_name,
                "args": args,
            }

            await self.event_queue.put(event)
            _logger.debug(f"工具调用开始: {tool_name} (run_id: {run_id})")

        except Exception:
            _logger.exception("处理 tool_start 事件时出错")

    async def on_tool_end(
        self,
        output: Any,
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """工具调用结束时触发

        发送 tool-result 事件到队列，格式：
        {
            "type": "tool-result",
            "toolCallId": "<run_id>",
            "result": <output>
        }

        Args:
            output: 工具输出结果
            run_id: 当前运行 ID
            parent_run_id: 父运行 ID
            tags: 标签列表
            **kwargs: 其他参数
        """
        try:
            tool_call_id = str(run_id)

            # 获取工具名称（用于日志）
            tool_name = self._tool_call_ids.pop(tool_call_id, "unknown_tool")

            # 处理输出：确保可序列化
            if isinstance(output, str):
                result = output
            elif hasattr(output, "content"):
                # LangChain ToolMessage 或类似对象
                result = output.content
            elif isinstance(output, dict):
                result = output
            else:
                # 尝试转换为字符串
                result = str(output)

            event = {
                "type": EventType.TOOL_RESULT,
                "toolCallId": tool_call_id,
                "result": result,
            }

            await self.event_queue.put(event)
            _logger.debug(f"工具调用完成: {tool_name} (run_id: {run_id})")

        except Exception:
            _logger.exception("处理 tool_end 事件时出错")

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """工具调用出错时触发

        发送 tool-result 事件（包含错误信息）到队列。

        Args:
            error: 异常对象
            run_id: 当前运行 ID
            parent_run_id: 父运行 ID
            tags: 标签列表
            **kwargs: 其他参数
        """
        try:
            tool_call_id = str(run_id)

            # 清理映射
            tool_name = self._tool_call_ids.pop(tool_call_id, "unknown_tool")

            event = {
                "type": EventType.TOOL_RESULT,
                "toolCallId": tool_call_id,
                "result": f"Error: {str(error)}",
            }

            await self.event_queue.put(event)
            _logger.warning(f"工具调用出错: {tool_name} - {error}")

        except Exception:
            _logger.exception("处理 tool_error 事件时出错")

    async def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Any = None,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """LLM 流式输出新 token 时触发

        这是处理 chat model 流式输出的正确回调方法。
        LangChain 在流式生成时调用此方法，对应 astream_events 中的 on_chat_model_stream 事件。

        发送 text-delta 事件到队列，格式：
        {
            "type": "text-delta",
            "id": "text-<message_id>",
            "delta": "<content>"
        }

        Args:
            token: 新生成的 token
            chunk: 数据块（可能包含额外信息）
            run_id: 当前运行 ID
            parent_run_id: 父运行 ID
            tags: 标签列表
            **kwargs: 其他参数
        """
        try:
            if token:
                self.full_content += token

                event = {
                    "type": EventType.TEXT_DELTA,
                    "id": f"text-{self.message_id}",
                    "delta": token,
                }

                await self.event_queue.put(event)
                _logger.debug(f"发送 text-delta: {token[:50]}...")

        except Exception:
            _logger.exception("处理 llm_new_token 事件时出错")
