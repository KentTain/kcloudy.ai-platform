"""UIMessageChunkCallbackHandler - 将 LangChain 事件转换为 AI SDK 格式

继承 LangChain AsyncCallbackHandler，拦截工具调用事件和 LLM 流式输出事件，
转换为 AI SDK UIMessageChunk 标准格式发送到事件队列。

事件映射：
- on_llm_new_token -> text-delta (LLM 流式输出)
- on_tool_start -> tool-call (工具调用开始)
- on_tool_end -> tool-result (工具调用结束)
- on_tool_error -> tool-result (工具调用错误)
- on_chain_start -> thinking-start (Agent 决策步骤)
- on_chain_end -> thinking-end (决策步骤结束)
- on_llm_start -> thinking-start (LLM 推理过程，非第一次调用)
- on_llm_end -> thinking-end (LLM 推理步骤结束)
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from langchain_core.callbacks import AsyncCallbackHandler
from loguru import logger

from ai.controllers.v1.chat.event_types import EventType
from extended.langchain.callbacks.reasoning_step_builder import ReasoningStepBuilder
from extended.langchain.callbacks.reasoning_types import ReasoningStepType

_logger = logger.bind(name=__name__)


class UIMessageChunkCallbackHandler(AsyncCallbackHandler):
    """将 LangChain 事件转换为 AI SDK UIMessageChunk 格式

    职责边界：
    - 监听 LangChain LLM 流式输出事件（on_llm_new_token）
    - 监听 LangChain 工具调用事件（on_tool_start, on_tool_end）
    - 监听 LangChain 推理步骤事件（on_chain_start, on_chain_end, on_llm_start, on_llm_end）
    - 转换为 AI SDK 标准格式（text-delta, tool-call, tool-result, thinking-*）
    - 发送到事件队列供 SSE 流消费

    架构设计：
    所有事件（包括文本流、工具调用和推理步骤）统一通过 CallbackHandler 处理，
    符合规格定义的单一路径架构：
    agent.astream_events() → UIMessageChunkCallbackHandler → event_queue

    不负责：
    - usage 统计（保留在 run_llm_task 中）
    - 数据库持久化
    """

    def __init__(
        self,
        event_queue: asyncio.Queue,
        message_id: str = "",
        thinking_config: dict[str, Any] | None = None,
    ) -> None:
        """初始化回调处理器

        Args:
            event_queue: 事件队列，用于发送 SSE 事件
            message_id: 消息 ID，用于生成 text-delta 事件的 id
            thinking_config: 思考过程功能配置
        """
        super().__init__()
        self.event_queue = event_queue
        self._tool_call_ids: dict[str, str] = {}  # run_id -> tool_call_id 映射
        self.message_id = message_id
        self.full_content = ""  # 累积文本内容

        # 思考过程功能配置
        self.thinking_enabled = thinking_config.get("enabled", True) if thinking_config else True
        self.reasoning_builder = ReasoningStepBuilder(event_queue) if self.thinking_enabled else None
        self.first_llm_call = True  # 标记是否是第一次 LLM 调用

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

    async def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """链式调用开始（Agent 决策、工具链等）

        捕获 Agent 的决策步骤和推理过程
        """
        if not self.thinking_enabled or not self.reasoning_builder:
            return

        try:
            # 判断是否是 Agent 决策步骤
            chain_name = serialized.get("name", "")

            # 检查是否为 Agent 或决策相关的链
            if self._is_agent_decision(chain_name, metadata):
                # 提取决策上下文
                decision_context = self._extract_decision_context(inputs)

                # 开始推理步骤
                await self.reasoning_builder.start_reasoning_step(
                    step_type=ReasoningStepType.DECISION,
                    title=f"决策: {chain_name}",
                    metadata={
                        "run_id": str(run_id),
                        "parent_run_id": str(parent_run_id) if parent_run_id else None,
                        "chain_name": chain_name,
                    }
                )

                # 输出决策内容
                if decision_context:
                    await self.reasoning_builder.append_reasoning_content(
                        f"分析输入: {decision_context}\n"
                    )

        except Exception:
            _logger.exception("处理 chain_start 事件时出错")

    async def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """链式调用结束"""
        if not self.thinking_enabled or not self.reasoning_builder:
            return

        try:
            # 结束当前活跃的推理步骤（如果有）
            if self.reasoning_builder.step_stack:
                # 输出决策结果
                if outputs:
                    result_summary = self._summarize_output(outputs)
                    await self.reasoning_builder.append_reasoning_content(
                        f"决策结果: {result_summary}\n"
                    )

                await self.reasoning_builder.end_reasoning_step()

        except Exception:
            _logger.exception("处理 chain_end 事件时出错")

    async def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用开始

        区分：
        - 第一次 LLM 调用：生成思考过程
        - 后续 LLM 调用：可能是工具调用后的分析
        """
        if not self.thinking_enabled or not self.reasoning_builder:
            return

        try:
            # 如果不是第一次调用，说明是工具调用后的推理
            if not self.first_llm_call:
                await self.reasoning_builder.start_reasoning_step(
                    step_type=ReasoningStepType.RESULT_ANALYSIS,
                    title="分析工具结果",
                    metadata={
                        "run_id": str(run_id),
                        "parent_run_id": str(parent_run_id) if parent_run_id else None,
                    }
                )

                # 输出分析提示
                if prompts:
                    prompt_summary = self._summarize_prompts(prompts)
                    await self.reasoning_builder.append_reasoning_content(
                        f"基于工具结果进行分析: {prompt_summary}\n"
                    )

            self.first_llm_call = False

        except Exception:
            _logger.exception("处理 llm_start 事件时出错")

    async def on_llm_end(
        self,
        response: Any,
        *,
        run_id: uuid.UUID,
        parent_run_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用结束"""
        if not self.thinking_enabled or not self.reasoning_builder:
            return

        try:
            # 结束推理步骤（如果有）
            if self.reasoning_builder.step_stack:
                await self.reasoning_builder.end_reasoning_step()

        except Exception:
            _logger.exception("处理 llm_end 事件时出错")

    def _is_agent_decision(self, chain_name: str, metadata: dict | None) -> bool:
        """判断是否是 Agent 决策步骤

        Args:
            chain_name: 链名称
            metadata: 元数据

        Returns:
            是否为决策步骤
        """
        # 检查名称中是否包含关键词
        decision_keywords = ["agent", "decision", "planner", "reasoning"]
        return any(kw in chain_name.lower() for kw in decision_keywords)

    def _extract_decision_context(self, inputs: dict[str, Any]) -> str:
        """提取决策上下文

        Args:
            inputs: 输入参数

        Returns:
            决策上下文字符串
        """
        if "input" in inputs:
            return str(inputs["input"])
        elif "query" in inputs:
            return str(inputs["query"])
        return ""

    def _summarize_output(self, outputs: dict[str, Any]) -> str:
        """总结输出内容

        Args:
            outputs: 输出字典

        Returns:
            输出摘要
        """
        if "output" in outputs:
            output = outputs["output"]
            if isinstance(output, str):
                return output[:100] + "..." if len(output) > 100 else output
        return "完成"

    def _summarize_prompts(self, prompts: list[str]) -> str:
        """总结提示内容

        Args:
            prompts: 提示列表

        Returns:
            提示摘要
        """
        if not prompts:
            return ""
        # 取第一个提示的前 100 字符
        first_prompt = prompts[0]
        return first_prompt[:100] + "..." if len(first_prompt) > 100 else first_prompt
