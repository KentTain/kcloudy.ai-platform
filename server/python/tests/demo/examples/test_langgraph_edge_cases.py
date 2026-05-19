"""
LangGraph 工作流边界条件测试

综合测试各种边界条件和异常场景。
"""

import pytest

from demo.examples.langgraph_workflows.intent_router_demo import (
    AgentState,
    IntentRouterWorkflow,
)
from demo.examples.langgraph_workflows.error_handler_demo import (
    CircuitBreakerWorkflow,
    ErrorCountState,
    ErrorHandlerWorkflow,
)
from demo.examples.langgraph_workflows.parallel_execution_demo import (
    ParallelState,
    SimpleParallelWorkflow,
)


class TestIntentRouterEdgeCases:
    """意图路由边界条件测试"""

    @pytest.fixture
    def workflow(self) -> IntentRouterWorkflow:
        """创建工作流实例"""
        return IntentRouterWorkflow()

    def test_empty_string_query(self, workflow: IntentRouterWorkflow) -> None:
        """测试空字符串查询"""
        result = workflow.run("")
        assert result["intent"] == "unknown"
        assert "抱歉" in result["result"]

    def test_whitespace_only_query(self, workflow: IntentRouterWorkflow) -> None:
        """测试仅空白字符查询"""
        result = workflow.run("   ")
        assert result["intent"] == "unknown"

    def test_very_long_query(self, workflow: IntentRouterWorkflow) -> None:
        """测试超长查询（10000字符）"""
        long_query = "天气" * 5000
        result = workflow.run(long_query)
        assert result["intent"] == "weather"

    def test_special_html_characters(self, workflow: IntentRouterWorkflow) -> None:
        """测试 HTML 特殊字符"""
        result = workflow.run("<script>alert('test')</script>")
        assert result is not None
        assert "intent" in result

    def test_sql_injection_attempt(self, workflow: IntentRouterWorkflow) -> None:
        """测试 SQL 注入尝试"""
        result = workflow.run("'; DROP TABLE users; --")
        assert result["intent"] == "unknown"

    def test_newline_characters(self, workflow: IntentRouterWorkflow) -> None:
        """测试换行字符"""
        result = workflow.run("今天天气\n怎么样？")
        assert result["intent"] == "weather"

    def test_unicode_emoji(self, workflow: IntentRouterWorkflow) -> None:
        """测试 Unicode 表情符号"""
        result = workflow.run("天气怎么样？ 🌤️")
        assert result["intent"] == "weather"

    def test_mixed_case_weather(self, workflow: IntentRouterWorkflow) -> None:
        """测试大小写混合"""
        result = workflow.run("WeAtHeR today")
        assert result["intent"] == "weather"

    def test_multiple_intents(self, workflow: IntentRouterWorkflow) -> None:
        """测试多意图混合"""
        # 天气关键词在前，应识别为天气
        result = workflow.run("今天天气如何，以及什么是AI？")
        assert result["intent"] == "weather"

    def test_numbers_only(self, workflow: IntentRouterWorkflow) -> None:
        """测试纯数字"""
        result = workflow.run("12345")
        assert result["intent"] == "unknown"

    def test_punctuation_only(self, workflow: IntentRouterWorkflow) -> None:
        """测试纯标点符号"""
        result = workflow.run("！@#￥%……&*（）")
        assert result["intent"] == "unknown"


class TestErrorHandlerEdgeCases:
    """错误处理边界条件测试"""

    @pytest.fixture
    def workflow(self) -> ErrorHandlerWorkflow:
        """创建工作流实例"""
        wf = ErrorHandlerWorkflow()
        wf.reset_failure_count()
        return wf

    def test_negative_error_count(self) -> None:
        """测试负错误计数"""
        state = ErrorCountState(query="测试", error_count=-1)
        assert state.error_count == -1

    def test_max_errors_zero(self) -> None:
        """测试零最大错误数"""
        state = ErrorCountState(query="测试", max_errors=0, error_count=0)
        assert state.max_errors == 0

    def test_max_errors_one(self) -> None:
        """测试最大错误数为1"""
        state = ErrorCountState(query="测试", max_errors=1, error_count=0)
        assert state.max_errors == 1

    def test_concurrent_state_modification(self) -> None:
        """测试并发状态修改概念"""
        # 模拟多个状态实例
        state1 = ErrorCountState(query="测试1")
        state2 = ErrorCountState(query="测试2")
        assert state1.query != state2.query


class TestParallelExecutionEdgeCases:
    """并行执行边界条件测试"""

    @pytest.fixture
    def workflow(self) -> SimpleParallelWorkflow:
        """创建工作流实例"""
        return SimpleParallelWorkflow()

    def test_empty_query(self, workflow: SimpleParallelWorkflow) -> None:
        """测试空查询"""
        result = workflow.run("")
        assert "results" in result
        assert len(result["results"]) == 3

    def test_null_character(self, workflow: SimpleParallelWorkflow) -> None:
        """测试空字符"""
        result = workflow.run("\x00测试")
        assert result is not None

    def test_very_long_query(self, workflow: SimpleParallelWorkflow) -> None:
        """测试超长查询"""
        long_query = "测试" * 5000
        result = workflow.run(long_query)
        assert result["query"] == long_query

    def test_repeated_queries(self, workflow: SimpleParallelWorkflow) -> None:
        """测试重复查询"""
        for _ in range(10):
            result = workflow.run("测试")
            assert "results" in result


class TestStateValidation:
    """状态验证测试"""

    def test_agent_state_serialization(self) -> None:
        """测试 AgentState 序列化"""
        state = AgentState(
            query="测试",
            intent="weather",
            result="结果",
            error_count=1,
            retry_flag=True,
        )
        data = state.model_dump()
        assert data["query"] == "测试"
        assert data["intent"] == "weather"

    def test_error_count_state_serialization(self) -> None:
        """测试 ErrorCountState 序列化"""
        state = ErrorCountState(
            query="测试",
            error_count=2,
            circuit_open=False,
        )
        data = state.model_dump()
        assert data["error_count"] == 2

    def test_parallel_state_serialization(self) -> None:
        """测试 ParallelState 序列化"""
        state = ParallelState(
            query="测试",
            results=[{"source": "wiki", "result": "内容"}],
        )
        data = state.model_dump()
        assert len(data["results"]) == 1


class TestPerformanceScenarios:
    """性能场景测试"""

    @pytest.fixture
    def workflow(self) -> IntentRouterWorkflow:
        """创建工作流实例"""
        return IntentRouterWorkflow()

    def test_rapid_queries(self, workflow: IntentRouterWorkflow) -> None:
        """测试快速连续查询"""
        queries = ["天气", "知识", "随机"] * 10
        for q in queries:
            result = workflow.run(q)
            assert result is not None

    def test_state_size_limit(self, workflow: IntentRouterWorkflow) -> None:
        """测试状态大小限制"""
        # 多次执行增加消息历史
        result = workflow.run("测试消息大小")
        assert len(result["messages"]) < 100  # 消息数应有限制
