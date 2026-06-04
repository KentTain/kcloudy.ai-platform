"""UIMessageChunkCallbackHandler 单元测试"""

import asyncio
import uuid

import pytest

from ai.controllers.v1.chat.event_types import EventType
from extended.langchain.callbacks import UIMessageChunkCallbackHandler


@pytest.fixture
def event_queue():
    """创建事件队列 fixture"""
    return asyncio.Queue()


@pytest.fixture
def callback_handler(event_queue):
    """创建回调处理器 fixture"""
    return UIMessageChunkCallbackHandler(event_queue, message_id="test-message-id")


class TestUIMessageChunkCallbackHandler:
    """UIMessageChunkCallbackHandler 测试类"""

    @pytest.mark.asyncio
    async def test_on_tool_start_sends_tool_call_event(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_tool_start 发送 tool-call 事件"""
        # 准备测试数据
        run_id = uuid.uuid4()
        serialized = {"name": "search_tool"}
        inputs = {"query": "test query"}

        # 执行回调
        await callback_handler.on_tool_start(
            serialized=serialized,
            input_str="",
            run_id=run_id,
            inputs=inputs,
        )

        # 验证事件
        event = event_queue.get_nowait()
        assert event["type"] == EventType.TOOL_CALL
        assert event["toolCallId"] == str(run_id)
        assert event["toolName"] == "search_tool"
        assert event["args"] == inputs

    @pytest.mark.asyncio
    async def test_on_tool_start_with_input_str(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_tool_start 使用 input_str"""
        run_id = uuid.uuid4()
        serialized = {"name": "calculator"}
        input_str = "2 + 2"

        await callback_handler.on_tool_start(
            serialized=serialized,
            input_str=input_str,
            run_id=run_id,
        )

        event = event_queue.get_nowait()
        assert event["type"] == EventType.TOOL_CALL
        assert event["toolName"] == "calculator"
        assert event["args"] == {"input": input_str}

    @pytest.mark.asyncio
    async def test_on_tool_start_with_missing_name(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_tool_start 工具名称缺失时使用默认值"""
        run_id = uuid.uuid4()
        serialized = {}

        await callback_handler.on_tool_start(
            serialized=serialized,
            input_str="test",
            run_id=run_id,
        )

        event = event_queue.get_nowait()
        assert event["toolName"] == "unknown_tool"

    @pytest.mark.asyncio
    async def test_on_tool_end_sends_tool_result_event(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_tool_end 发送 tool-result 事件"""
        # 先注册一个工具调用
        run_id = uuid.uuid4()
        callback_handler._tool_call_ids[str(run_id)] = "test_tool"

        # 执行回调
        await callback_handler.on_tool_end(
            output="tool output",
            run_id=run_id,
        )

        # 验证事件
        event = event_queue.get_nowait()
        assert event["type"] == EventType.TOOL_RESULT
        assert event["toolCallId"] == str(run_id)
        assert event["result"] == "tool output"

        # 验证清理映射
        assert str(run_id) not in callback_handler._tool_call_ids

    @pytest.mark.asyncio
    async def test_on_tool_end_with_dict_output(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_tool_end 处理字典输出"""
        run_id = uuid.uuid4()
        callback_handler._tool_call_ids[str(run_id)] = "test_tool"
        output_dict = {"status": "success", "data": [1, 2, 3]}

        await callback_handler.on_tool_end(
            output=output_dict,
            run_id=run_id,
        )

        event = event_queue.get_nowait()
        assert event["result"] == output_dict

    @pytest.mark.asyncio
    async def test_on_tool_end_with_content_attribute(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_tool_end 处理带有 content 属性的对象"""

        # 模拟 ToolMessage
        class MockToolMessage:
            content = "tool message content"

        run_id = uuid.uuid4()
        callback_handler._tool_call_ids[str(run_id)] = "test_tool"

        await callback_handler.on_tool_end(
            output=MockToolMessage(),
            run_id=run_id,
        )

        event = event_queue.get_nowait()
        assert event["result"] == "tool message content"

    @pytest.mark.asyncio
    async def test_on_tool_error_sends_tool_result_with_error(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_tool_error 发送包含错误信息的 tool-result 事件"""
        run_id = uuid.uuid4()
        callback_handler._tool_call_ids[str(run_id)] = "failing_tool"

        await callback_handler.on_tool_error(
            error=ValueError("Something went wrong"),
            run_id=run_id,
        )

        event = event_queue.get_nowait()
        assert event["type"] == EventType.TOOL_RESULT
        assert "Error: Something went wrong" in event["result"]

        # 验证清理映射
        assert str(run_id) not in callback_handler._tool_call_ids

    @pytest.mark.asyncio
    async def test_tool_call_flow(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试完整的工具调用流程"""
        run_id = uuid.uuid4()

        # 1. 工具开始
        await callback_handler.on_tool_start(
            serialized={"name": "weather_tool"},
            input_str="",
            run_id=run_id,
            inputs={"city": "Beijing"},
        )

        event1 = event_queue.get_nowait()
        assert event1["type"] == EventType.TOOL_CALL
        assert event1["toolName"] == "weather_tool"
        assert event1["args"] == {"city": "Beijing"}

        # 2. 工具结束
        await callback_handler.on_tool_end(
            output="Sunny, 25°C",
            run_id=run_id,
        )

        event2 = event_queue.get_nowait()
        assert event2["type"] == EventType.TOOL_RESULT
        assert event2["result"] == "Sunny, 25°C"

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试多个工具调用"""
        run_id_1 = uuid.uuid4()
        run_id_2 = uuid.uuid4()

        # 工具 1 开始
        await callback_handler.on_tool_start(
            serialized={"name": "tool_1"},
            input_str="",
            run_id=run_id_1,
        )

        # 工具 2 开始
        await callback_handler.on_tool_start(
            serialized={"name": "tool_2"},
            input_str="",
            run_id=run_id_2,
        )

        # 工具 1 结束
        await callback_handler.on_tool_end(
            output="result_1",
            run_id=run_id_1,
        )

        # 工具 2 结束
        await callback_handler.on_tool_end(
            output="result_2",
            run_id=run_id_2,
        )

        # 验证事件顺序
        events = []
        while not event_queue.empty():
            events.append(event_queue.get_nowait())

        assert len(events) == 4
        assert events[0]["type"] == EventType.TOOL_CALL
        assert events[0]["toolName"] == "tool_1"
        assert events[1]["type"] == EventType.TOOL_CALL
        assert events[1]["toolName"] == "tool_2"
        assert events[2]["type"] == EventType.TOOL_RESULT
        assert events[2]["result"] == "result_1"
        assert events[3]["type"] == EventType.TOOL_RESULT
        assert events[3]["result"] == "result_2"

    @pytest.mark.asyncio
    async def test_on_llm_new_token_sends_text_delta_event(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_llm_new_token 发送 text-delta 事件"""

        run_id = uuid.uuid4()
        token = "Hello"

        await callback_handler.on_llm_new_token(
            token=token,
            run_id=run_id,
        )

        event = event_queue.get_nowait()
        assert event["type"] == EventType.TEXT_DELTA
        assert event["id"] == "text-test-message-id"
        assert event["delta"] == "Hello"

        # 验证内容已累积
        assert callback_handler.full_content == "Hello"

    @pytest.mark.asyncio
    async def test_text_delta_format_matches_ai_sdk_spec(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 text-delta 格式符合 AI SDK 规范"""

        run_id = uuid.uuid4()

        # 发送多个 token
        await callback_handler.on_llm_new_token(
            token="第一段",
            run_id=run_id,
        )

        await callback_handler.on_llm_new_token(
            token="第二段",
            run_id=run_id,
        )

        # 验证事件格式
        event1 = event_queue.get_nowait()
        assert event1["type"] == EventType.TEXT_DELTA
        assert "id" in event1
        assert "delta" in event1
        assert event1["delta"] == "第一段"

        event2 = event_queue.get_nowait()
        assert event2["type"] == EventType.TEXT_DELTA
        assert event2["delta"] == "第二段"

        # 验证内容累积
        assert callback_handler.full_content == "第一段第二段"

    @pytest.mark.asyncio
    async def test_on_llm_new_token_with_empty_token(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试 on_llm_new_token 空 token 不发送事件"""

        run_id = uuid.uuid4()

        await callback_handler.on_llm_new_token(
            token="",
            run_id=run_id,
        )

        # 不应有事件发送
        assert event_queue.empty()
        assert callback_handler.full_content == ""

    @pytest.mark.asyncio
    async def test_mixed_events_flow(
        self, callback_handler: UIMessageChunkCallbackHandler, event_queue: asyncio.Queue
    ):
        """测试文本流和工具调用混合场景"""

        run_id_1 = uuid.uuid4()
        run_id_2 = uuid.uuid4()

        # 1. 发送文本内容
        await callback_handler.on_llm_new_token(
            token="AI 回复",
            run_id=run_id_1,
        )

        # 2. 工具调用开始
        await callback_handler.on_tool_start(
            serialized={"name": "search"},
            input_str="",
            run_id=run_id_2,
            inputs={"query": "test"},
        )

        # 3. 工具调用结束
        await callback_handler.on_tool_end(
            output="search result",
            run_id=run_id_2,
        )

        # 验证事件顺序
        events = []
        while not event_queue.empty():
            events.append(event_queue.get_nowait())

        assert len(events) == 3
        assert events[0]["type"] == EventType.TEXT_DELTA
        assert events[0]["delta"] == "AI 回复"
        assert events[1]["type"] == EventType.TOOL_CALL
        assert events[1]["toolName"] == "search"
        assert events[2]["type"] == EventType.TOOL_RESULT
        assert events[2]["result"] == "search result"
