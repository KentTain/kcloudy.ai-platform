"""SSE Generator 思考过程事件处理测试"""

import asyncio

import pytest

from ai.controllers.v1.chat.event_types import EventType
from ai.controllers.v1.chat.llm import _sse_generator


@pytest.fixture
def event_queue():
    """创建事件队列 fixture"""
    return asyncio.Queue()


@pytest.mark.asyncio
class TestSSEGeneratorThinkingEvents:
    """SSE Generator 思考过程事件测试"""

    async def test_thinking_start_event(self, event_queue: asyncio.Queue):
        """测试思考开始事件"""
        message_id = "test-message-id"

        # 添加思考开始事件
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-123",
            "stepType": "reasoning",
            "title": "分析问题"
        })
        await event_queue.put(None)  # 结束信号

        # 收集 SSE 输出
        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证思考开始事件被正确转发
        assert any("thinking-start" in line for line in outputs)
        assert any("thinking-123" in line for line in outputs)
        assert any("分析问题" in line for line in outputs)

    async def test_thinking_delta_event(self, event_queue: asyncio.Queue):
        """测试思考增量事件"""
        message_id = "test-message-id"

        # 添加思考事件序列
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-123",
            "stepType": "reasoning",
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-123",
            "delta": "正在分析问题..."
        })
        await event_queue.put({
            "type": EventType.THINKING_END,
            "id": "thinking-123",
        })
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证思考增量事件被正确转发
        assert any("thinking-delta" in line for line in outputs)
        assert any("正在分析问题..." in line for line in outputs)

    async def test_thinking_end_event(self, event_queue: asyncio.Queue):
        """测试思考结束事件"""
        message_id = "test-message-id"

        # 添加思考事件序列
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-123",
            "stepType": "reasoning",
        })
        await event_queue.put({
            "type": EventType.THINKING_END,
            "id": "thinking-123",
        })
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证思考结束事件被正确转发
        assert any("thinking-end" in line for line in outputs)

    async def test_thinking_auto_close_before_finish(self, event_queue: asyncio.Queue):
        """测试思考块在 FINISH 前自动关闭"""
        message_id = "test-message-id"

        # 添加思考开始事件但不添加结束事件
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-123",
            "stepType": "reasoning",
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-123",
            "delta": "思考内容"
        })
        # 直接发送 FINISH 事件（模拟异常情况）
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
        thinking_end_found = False
        finish_found = False

        for line in outputs:
            if "thinking-end" in line:
                thinking_end_found = True
            if '"type":"finish"' in line:
                finish_found = True
                # FINISH 前应该已经有 thinking-end
                assert thinking_end_found, "思考块应在 FINISH 前关闭"

        assert thinking_end_found, "应发送 thinking-end 事件"
        assert finish_found, "应发送 finish 事件"

    async def test_multiple_thinking_steps(self, event_queue: asyncio.Queue):
        """测试多个思考步骤"""
        message_id = "test-message-id"

        # 第一个思考步骤
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-1",
            "stepType": "decision",
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-1",
            "delta": "决策步骤 1"
        })
        await event_queue.put({
            "type": EventType.THINKING_END,
            "id": "thinking-1",
        })

        # 第二个思考步骤
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-2",
            "stepType": "result_analysis",
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-2",
            "delta": "分析步骤 2"
        })
        await event_queue.put({
            "type": EventType.THINKING_END,
            "id": "thinking-2",
        })
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证两个思考步骤都被正确处理
        assert sum(1 for line in outputs if "thinking-start" in line) == 2
        assert sum(1 for line in outputs if "thinking-end" in line) == 2

    async def test_thinking_and_text_mixed(self, event_queue: asyncio.Queue):
        """测试思考和文本混合场景"""
        message_id = "test-message-id"

        # 思考过程
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-123",
            "stepType": "reasoning",
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-123",
            "delta": "分析中..."
        })
        await event_queue.put({
            "type": EventType.THINKING_END,
            "id": "thinking-123",
        })

        # 文本内容
        await event_queue.put({
            "type": EventType.TEXT_DELTA,
            "id": "text-456",
            "delta": "回答内容"
        })
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证思考和文本事件都被正确处理
        thinking_events = [line for line in outputs if "thinking-" in line]
        text_events = [line for line in outputs if "text-" in line]

        assert len(thinking_events) > 0, "应包含思考事件"
        assert len(text_events) > 0, "应包含文本事件"

    async def test_nested_thinking_steps(self, event_queue: asyncio.Queue):
        """测试嵌套思考步骤"""
        message_id = "test-message-id"

        # 外层思考步骤
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-1",
            "stepType": "decision",
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-1",
            "delta": "外层决策"
        })

        # 内层思考步骤（嵌套）
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-2",
            "stepType": "tool_selection",
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-2",
            "delta": "选择工具"
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

        # 验证嵌套思考步骤被正确处理
        assert sum(1 for line in outputs if "thinking-start" in line) == 2
        assert sum(1 for line in outputs if "thinking-end" in line) == 2

    async def test_thinking_events_preserve_metadata(self, event_queue: asyncio.Queue):
        """测试思考事件保留元数据"""
        message_id = "test-message-id"

        # 添加带完整元数据的思考事件
        await event_queue.put({
            "type": EventType.THINKING_START,
            "id": "thinking-123",
            "stepType": "decision",
            "title": "决策步骤",
            "parentId": None,
        })
        await event_queue.put({
            "type": EventType.THINKING_DELTA,
            "id": "thinking-123",
            "delta": "决策内容"
        })
        await event_queue.put({
            "type": EventType.THINKING_END,
            "id": "thinking-123",
        })
        await event_queue.put(None)

        outputs = []
        async for line in _sse_generator(event_queue, message_id):
            outputs.append(line)

        # 验证元数据被保留
        assert any("决策步骤" in line for line in outputs)
        assert any("decision" in line for line in outputs)
