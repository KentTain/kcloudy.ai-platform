"""
异常处理工作流单元测试

测试 error_handler_demo 模块的所有功能。
"""

import pytest

from demo.examples.langgraph_workflows.error_handler_demo import (
    CircuitBreakerWorkflow,
    ErrorCountState,
    ErrorHandlerWorkflow,
    circuit_breaker_check,
    error_count_node,
    fallback_node,
)


class TestErrorCountState:
    """测试错误计数状态模型"""

    def test_state_initialization(self) -> None:
        """测试状态初始化"""
        state = ErrorCountState(query="测试")
        assert state.query == "测试"
        assert state.error_count == 0
        assert state.max_errors == 3
        assert state.circuit_open is False
        assert state.retry_flag is False

    def test_state_with_errors(self) -> None:
        """测试带错误计数的状态"""
        state = ErrorCountState(query="测试", error_count=2)
        assert state.error_count == 2


class TestErrorCountNode:
    """测试错误计数节点"""

    def test_first_error(self) -> None:
        """测试第一次错误"""
        state = ErrorCountState(query="测试")
        result = error_count_node(state)
        assert result["error_count"] == 1
        assert result["circuit_open"] is False
        assert result["retry_flag"] is True

    def test_reaching_max_errors(self) -> None:
        """测试达到最大错误数"""
        state = ErrorCountState(query="测试", error_count=2)
        result = error_count_node(state)
        assert result["error_count"] == 3
        assert result["circuit_open"] is True
        assert result["retry_flag"] is False

    def test_exceeding_max_errors(self) -> None:
        """测试超过最大错误数"""
        state = ErrorCountState(query="测试", error_count=5)
        result = error_count_node(state)
        assert result["circuit_open"] is True


class TestCircuitBreakerCheck:
    """测试熔断检查函数"""

    def test_circuit_closed(self) -> None:
        """测试熔断关闭状态"""
        state = ErrorCountState(query="测试", circuit_open=False)
        result = circuit_breaker_check(state)
        assert result == "mock_tool_node"

    def test_circuit_open(self) -> None:
        """测试熔断开启状态"""
        state = ErrorCountState(query="测试", circuit_open=True)
        result = circuit_breaker_check(state)
        assert result == "fallback_node"


class TestFallbackNode:
    """测试降级处理节点"""

    def test_fallback_response(self) -> None:
        """测试降级响应"""
        state = ErrorCountState(query="测试查询", error_count=3)
        result = fallback_node(state)
        assert "抱歉" in result["result"]
        assert "服务暂时不可用" in result["result"]
        assert "3" in result["result"]


class TestErrorHandlerWorkflow:
    """测试错误处理工作流"""

    @pytest.fixture
    def workflow(self) -> ErrorHandlerWorkflow:
        """创建工作流实例"""
        wf = ErrorHandlerWorkflow()
        wf.reset_failure_count()
        return wf

    def test_workflow_creation(self, workflow: ErrorHandlerWorkflow) -> None:
        """测试工作流创建"""
        assert workflow.app is not None

    def test_workflow_execution(self, workflow: ErrorHandlerWorkflow) -> None:
        """测试工作流执行"""
        result = workflow.run("测试查询")
        assert "error_count" in result
        assert "circuit_open" in result


class TestCircuitBreakerWorkflow:
    """测试熔断工作流"""

    @pytest.fixture
    def workflow(self) -> CircuitBreakerWorkflow:
        """创建工作流实例"""
        wf = CircuitBreakerWorkflow()
        wf.reset()
        return wf

    def test_workflow_creation(self, workflow: CircuitBreakerWorkflow) -> None:
        """测试工作流创建"""
        assert workflow.app is not None

    def test_circuit_breaker_trigger(self, workflow: CircuitBreakerWorkflow) -> None:
        """测试熔断触发"""
        result = workflow.run("测试")
        # 由于模拟失败，可能会触发熔断或成功
        assert "error_count" in result


class TestEdgeCases:
    """边界条件测试"""

    @pytest.fixture
    def workflow(self) -> ErrorHandlerWorkflow:
        """创建工作流实例"""
        wf = ErrorHandlerWorkflow()
        wf.reset_failure_count()
        return wf

    def test_zero_max_errors(self) -> None:
        """测试零错误阈值"""
        state = ErrorCountState(query="测试", max_errors=0)
        result = error_count_node(state)
        assert result["circuit_open"] is True

    def test_high_max_errors(self) -> None:
        """测试高错误阈值"""
        state = ErrorCountState(query="测试", max_errors=100)
        result = error_count_node(state)
        assert result["circuit_open"] is False

    def test_empty_query(self, workflow: ErrorHandlerWorkflow) -> None:
        """测试空查询"""
        result = workflow.run("")
        assert result is not None
