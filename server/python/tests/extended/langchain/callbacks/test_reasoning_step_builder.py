# server/python/tests/extended/langchain/callbacks/test_reasoning_step_builder.py

import asyncio
import pytest
from extended.langchain.callbacks.reasoning_step_builder import ReasoningStepBuilder
from extended.langchain.callbacks.reasoning_types import ReasoningStepType
from ai.controllers.v1.chat.event_types import EventType


@pytest.fixture
def event_queue():
    """创建事件队列 fixture"""
    return asyncio.Queue()


@pytest.fixture
def builder(event_queue):
    """创建 ReasoningStepBuilder fixture"""
    return ReasoningStepBuilder(event_queue)


class TestReasoningStepBuilderInit:
    """ReasoningStepBuilder 初始化测试"""

    def test_init_with_event_queue(self, event_queue):
        """测试使用事件队列初始化"""
        builder = ReasoningStepBuilder(event_queue)

        assert builder.event_queue == event_queue
        assert builder.step_stack == []
        assert builder._pending_deltas == []
        assert len(builder.sensitive_keywords) > 0

    def test_max_reasoning_depth_constant(self, builder):
        """测试最大推理深度常量"""
        assert ReasoningStepBuilder.MAX_REASONING_DEPTH == 10
        assert ReasoningStepBuilder.MAX_THINKING_LENGTH == 10000
        assert ReasoningStepBuilder.BATCH_SIZE == 5
        assert ReasoningStepBuilder.BATCH_INTERVAL == 0.1


class TestReasoningStepBuilderStartStep:
    """start_reasoning_step 测试"""

    @pytest.mark.asyncio
    async def test_start_reasoning_step_sends_event(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试开始推理步骤发送 thinking-start 事件"""
        step_id = await builder.start_reasoning_step(
            step_type=ReasoningStepType.REASONING,
            title="分析问题"
        )

        assert step_id is not None
        assert step_id.startswith("thinking-")

        # 验证事件
        event = event_queue.get_nowait()
        assert event["type"] == EventType.THINKING_START
        assert event["id"] == step_id
        assert event["title"] == "分析问题"
        assert event["stepType"] == "reasoning"

    @pytest.mark.asyncio
    async def test_start_reasoning_step_adds_to_stack(
        self, builder: ReasoningStepBuilder
    ):
        """测试开始推理步骤添加到栈"""
        step_id = await builder.start_reasoning_step(
            step_type=ReasoningStepType.DECISION
        )

        assert len(builder.step_stack) == 1
        assert builder.step_stack[0].id == step_id
        assert builder.step_stack[0].step_type == ReasoningStepType.DECISION

    @pytest.mark.asyncio
    async def test_start_reasoning_step_max_depth_limit(
        self, builder: ReasoningStepBuilder
    ):
        """测试最大深度限制"""
        # 超过最大深度
        for i in range(15):
            step_id = await builder.start_reasoning_step(
                step_type=ReasoningStepType.REASONING
            )

            if i < ReasoningStepBuilder.MAX_REASONING_DEPTH:
                assert step_id is not None
            else:
                # 超过深度限制，应该返回空字符串
                assert step_id == ""

        # 栈深度应该被限制
        assert len(builder.step_stack) == ReasoningStepBuilder.MAX_REASONING_DEPTH


class TestReasoningStepBuilderAppendContent:
    """append_reasoning_content 测试"""

    @pytest.mark.asyncio
    async def test_append_reasoning_content_sends_delta(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试追加思考内容发送 thinking-delta 事件"""
        # 先开始一个步骤
        step_id = await builder.start_reasoning_step(
            step_type=ReasoningStepType.REASONING
        )

        # 清空队列（移除 thinking-start）
        event_queue.get_nowait()

        # 追加足够多的内容触发批量发送（BATCH_SIZE = 5）
        for i in range(5):
            await builder.append_reasoning_content(f"思考内容{i}")

        # 验证 delta 事件
        event = event_queue.get_nowait()
        assert event["type"] == EventType.THINKING_DELTA
        assert event["id"] == step_id
        assert "思考内容" in event["delta"]

    @pytest.mark.asyncio
    async def test_append_reasoning_content_filters_sensitive_keywords(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试敏感关键词过滤"""
        await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        event_queue.get_nowait()  # 清空

        # 测试 API Key 过滤
        await builder.append_reasoning_content("api_key=sk-1234567890")
        assert event_queue.empty()  # 应该被过滤，不发送事件

    @pytest.mark.asyncio
    async def test_append_reasoning_content_filters_api_key_pattern(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试 API Key 格式过滤"""
        await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        event_queue.get_nowait()

        # 测试 API Key 正则匹配
        await builder.append_reasoning_content("key: sk-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGH")
        assert event_queue.empty()

    @pytest.mark.asyncio
    async def test_append_reasoning_content_filters_json_field(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试 JSON 字段过滤"""
        await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        event_queue.get_nowait()

        # 测试 JSON 字段检测
        await builder.append_reasoning_content('{"api_key": "secret123"}')
        assert event_queue.empty()

    @pytest.mark.asyncio
    async def test_append_reasoning_content_normal_content(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试正常内容通过"""
        await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        event_queue.get_nowait()

        # 测试正常内容（追加足够多触发批量发送）
        for i in range(5):
            await builder.append_reasoning_content(f"正常思考内容{i}")

        event = event_queue.get_nowait()
        assert "正常思考内容" in event["delta"]


class TestReasoningStepBuilderEndStep:
    """end_reasoning_step 测试"""

    @pytest.mark.asyncio
    async def test_end_reasoning_step_sends_end_event(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试结束推理步骤发送 thinking-end 事件"""
        step_id = await builder.start_reasoning_step(
            step_type=ReasoningStepType.DECISION
        )

        # 清空队列
        while not event_queue.empty():
            event_queue.get_nowait()

        # 结束步骤
        await builder.end_reasoning_step()

        # 验证 end 事件
        event = event_queue.get_nowait()
        assert event["type"] == EventType.THINKING_END
        assert event["id"] == step_id

    @pytest.mark.asyncio
    async def test_end_reasoning_step_pops_from_stack(
        self, builder: ReasoningStepBuilder
    ):
        """测试结束推理步骤从栈弹出"""
        await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        assert len(builder.step_stack) == 1

        await builder.end_reasoning_step()
        assert len(builder.step_stack) == 0

    @pytest.mark.asyncio
    async def test_end_reasoning_step_with_pending_deltas(
        self, builder: ReasoningStepBuilder, event_queue: asyncio.Queue
    ):
        """测试结束步骤时发送剩余 delta"""
        step_id = await builder.start_reasoning_step(step_type=ReasoningStepType.REASONING)
        event_queue.get_nowait()  # 清空 start

        # 追加少量内容（不触发批量发送）
        for i in range(3):  # 小于 BATCH_SIZE (5)
            await builder.append_reasoning_content(f"内容{i}")

        # 队列应该没有事件（未达到批量阈值）
        # 但在 end_reasoning_step 时应该发送

        # 清空队列
        while not event_queue.empty():
            event_queue.get_nowait()

        # 结束步骤
        await builder.end_reasoning_step()

        # 应该有一个 delta 事件（批量发送剩余内容）
        delta_event = event_queue.get_nowait()
        assert delta_event["type"] == EventType.THINKING_DELTA

        # 然后是 end 事件
        end_event = event_queue.get_nowait()
        assert end_event["type"] == EventType.THINKING_END
