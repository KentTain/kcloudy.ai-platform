# server/python/tests/ai/unit/controllers/v1/chat/test_event_types.py

import pytest
from ai.controllers.v1.chat.event_types import EventType


class TestEventTypeThinking:
    """EventType 思考事件测试"""

    def test_thinking_start_event_type(self):
        """测试 THINKING_START 事件类型"""
        assert hasattr(EventType, "THINKING_START")
        assert EventType.THINKING_START.value == "thinking-start"

    def test_thinking_delta_event_type(self):
        """测试 THINKING_DELTA 事件类型"""
        assert hasattr(EventType, "THINKING_DELTA")
        assert EventType.THINKING_DELTA.value == "thinking-delta"

    def test_thinking_end_event_type(self):
        """测试 THINKING_END 事件类型"""
        assert hasattr(EventType, "THINKING_END")
        assert EventType.THINKING_END.value == "thinking-end"

    def test_all_event_types_count(self):
        """测试事件类型总数"""
        # 原有 8 个 + 思考 3 个 + 新增 6 个 = 17 个
        assert len(EventType) == 17
