"""AI 对话思考过程集成测试

测试完整的 SSE 事件流，验证思考过程功能端到端工作正常。
"""

import asyncio

import pytest

from ai.controllers.v1.chat.event_types import EventType
from ai.controllers.v1.chat.llm import _sse_generator
from extended.langchain.callbacks import UIMessageChunkCallbackHandler
from extended.langchain.callbacks.reasoning_types import ReasoningStepType


@pytest.mark.asyncio
class TestThinkingProcessIntegration:
    """思考过程集成测试"""

    async def test_complete_sse_event_flow(self):
        """测试完整的 SSE 事件流"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        # 模拟完整的事件流
        events = [
            # 思考过程
            {
                "type": EventType.THINKING_START,
                "id": "thinking-1",
                "stepType": ReasoningStepType.DECISION,
                "title": "分析问题",
            },
            {
                "type": EventType.THINKING_DELTA,
                "id": "thinking-1",
                "delta": "正在分析用户的问题...",
            },
            {
                "type": EventType.THINKING_END,
                "id": "thinking-1",
            },
            # 工具调用
            {
                "type": EventType.TOOL_CALL,
                "toolCallId": "tool-1",
                "toolName": "search",
                "args": {"query": "test"},
            },
            {
                "type": EventType.TOOL_RESULT,
                "toolCallId": "tool-1",
                "result": "search result",
            },
            # 文本内容
            {
                "type": EventType.TEXT_DELTA,
                "id": "text-123",
                "delta": "AI 回复内容",
            },
            # 结束
            {
                "type": EventType.FINISH,
                "finishReason": "stop",
                "usage": {"promptTokens": 10, "completionTokens": 20},
            },
        ]

        # 添加事件到队列
        for event in events:
            await event_queue.put(event)
        await event_queue.put(None)  # 结束信号

        # 收集 SSE 输出
        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证事件顺序
        assert any("thinking-start" in line for line in outputs)
        assert any("thinking-delta" in line for line in outputs)
        assert any("thinking-end" in line for line in outputs)
        assert any("tool-call" in line for line in outputs)
        assert any("tool-result" in line for line in outputs)
        assert any("text-delta" in line for line in outputs)
        assert any('"type":"finish"' in line for line in outputs)

    async def test_thinking_events_order(self):
        """测试思考事件顺序验证"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        # 添加思考事件（确保正确顺序）
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-1",
            "stepType": ReasoningStepType.REASONING,
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-1",
            "delta": "推理内容",
        })
        await event_queue.put({
            "type": EventType.THINKING_END,
            "id": "thinking-1",
        })
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证事件顺序
        thinking_start_index = next(i for i, line in enumerate(outputs) if "thinking-start" in line)
        thinking_delta_index = next(i for i, line in enumerate(outputs) if "thinking-delta" in line)
        thinking_end_index = next(i for i, line in enumerate(outputs) if "thinking-end" in line)

        assert thinking_start_index < thinking_delta_index < thinking_end_index

    async def test_nested_reasoning_steps(self):
        """测试嵌套推理步骤"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        # 外层思考步骤
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-1",
            "stepType": ReasoningStepType.DECISION,
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-1",
            "delta": "外层决策",
        })

        # 内层思考步骤
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-2",
            "stepType": ReasoningStepType.TOOL_SELECTION,
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-2",
            "delta": "选择工具",
        })
        await event_queue.put({
            "type": EventType.THINKING_END,
            "id": "thinking-2",
        })

        # 关闭外层
        await event_queue.put({
            "type": EventType.THINKING_END,
            "id": "thinking-1",
        })
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证嵌套步骤被正确处理
        thinking_start_count = sum(1 for line in outputs if "thinking-start" in line)
        thinking_end_count = sum(1 for line in outputs if "thinking-end" in line)

        assert thinking_start_count == 2
        assert thinking_end_count == 2

    async def test_sensitive_info_filtering(self):
        """测试敏感信息过滤效果"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        # 添加包含敏感信息的思考内容
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-1",
            "stepType": ReasoningStepType.REASONING,
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-1",
            "delta": "API Key: sk-1234567890abcdefghijklmnopqrstuvwxyz1234567890",
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-1",
            "delta": "Password: secret123",
        })
        await event_queue.put({
            "type": EventType.THINKING_END,
            "id": "thinking-1",
        })
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证敏感信息被过滤（在 SSE 层不负责过滤，由 ReasoningStepBuilder 负责）
        # 这里只验证事件能够正常传输
        assert any("thinking-delta" in line for line in outputs)

    async def test_thinking_auto_close_on_finish(self):
        """测试 FINISH 事件前自动关闭思考块"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        # 添加思考开始但不添加结束事件
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-1",
            "stepType": ReasoningStepType.REASONING,
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-1",
            "delta": "思考内容",
        })
        # 直接发送 FINISH 事件
        await event_queue.put({
            "type": EventType.FINISH,
            "finishReason": "stop",
            "usage": {"promptTokens": 10, "completionTokens": 20},
        })
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证思考块在 FINISH 前被自动关闭
        thinking_end_index = next((i for i, line in enumerate(outputs) if "thinking-end" in line), None)
        finish_index = next(i for i, line in enumerate(outputs) if '"type":"finish"' in line)

        assert thinking_end_index is not None
        assert thinking_end_index < finish_index

    async def test_callback_handler_integration(self):
        """测试 CallbackHandler 集成"""
        event_queue = asyncio.Queue()
        message_id = "test-message-id"

        # 创建 CallbackHandler
        callback_handler = UIMessageChunkCallbackHandler(
            event_queue=event_queue,
            message_id=message_id,
            thinking_config={"enabled": True},
        )

        # 验证初始化
        assert callback_handler.thinking_enabled is True
        assert callback_handler.reasoning_builder is not None
        assert callback_handler.first_llm_call is True
