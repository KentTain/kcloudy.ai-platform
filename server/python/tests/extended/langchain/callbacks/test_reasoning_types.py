# server/python/tests/extended/langchain/callbacks/test_reasoning_types.py

import pytest
from datetime import datetime
from extended.langchain.callbacks.reasoning_types import ReasoningStepType, ReasoningStep


class TestReasoningStepType:
    """ReasoningStepType 枚举测试"""

    def test_reasoning_step_type_values(self):
        """测试枚举值正确"""
        assert ReasoningStepType.REASONING.value == "reasoning"
        assert ReasoningStepType.DECISION.value == "decision"
        assert ReasoningStepType.TOOL_SELECTION.value == "tool_selection"
        assert ReasoningStepType.TOOL_EXECUTION.value == "tool_execution"
        assert ReasoningStepType.RESULT_ANALYSIS.value == "result_analysis"
        assert ReasoningStepType.ERROR_HANDLING.value == "error_handling"

    def test_reasoning_step_type_string_conversion(self):
        """测试字符串转换"""
        assert ReasoningStepType.REASONING.value == "reasoning"
        assert ReasoningStepType("decision") == ReasoningStepType.DECISION


class TestReasoningStep:
    """ReasoningStep 数据类测试"""

    def test_reasoning_step_default_values(self):
        """测试默认值"""
        step = ReasoningStep()
        assert step.id.startswith("thinking-")
        assert step.step_type == ReasoningStepType.REASONING
        assert step.title is None
        assert step.content == ""
        assert step.parent_id is None
        assert step.metadata == {}
        assert isinstance(step.created_at, datetime)

    def test_reasoning_step_custom_values(self):
        """测试自定义值"""
        step = ReasoningStep(
            step_type=ReasoningStepType.DECISION,
            title="分析问题",
            content="正在分析用户输入",
            parent_id="thinking-parent",
            metadata={"key": "value"},
        )
        assert step.step_type == ReasoningStepType.DECISION
        assert step.title == "分析问题"
        assert step.content == "正在分析用户输入"
        assert step.parent_id == "thinking-parent"
        assert step.metadata == {"key": "value"}

    def test_reasoning_step_to_dict(self):
        """测试转换为字典"""
        step = ReasoningStep(
            id="thinking-test",
            step_type=ReasoningStepType.TOOL_SELECTION,
            title="选择工具",
            content="选择天气查询工具",
        )
        result = step.to_dict()

        assert result["id"] == "thinking-test"
        assert result["stepType"] == "tool_selection"
        assert result["title"] == "选择工具"
        assert result["delta"] == "选择天气查询工具"

