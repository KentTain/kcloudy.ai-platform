"""
异常处理与熔断机制示例

演示如何使用 LangGraph 构建具有容错能力的工作流。
包括：错误计数、熔断机制、自动降级处理。

Day 5 讲义：AI 智能体应用实战 - 工作流深化设计
"""

from typing import Annotated, Any, Literal

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

# ==================== 状态定义 ====================


class ErrorCountState(BaseModel):
    """
    错误计数状态

    用于追踪错误次数和控制熔断。
    """

    # 输入数据
    query: str = ""

    # 处理结果
    result: str = ""

    # 错误计数
    error_count: int = 0

    # 熔断阈值
    max_errors: int = 3

    # 是否触发熔断
    circuit_open: bool = False

    # 重试标志
    retry_flag: bool = False

    # 消息历史
    messages: Annotated[list[str], "消息列表"] = []


# ==================== 模拟失败的工具节点 ====================

# 控制模拟失败的计数器
_failure_count = 0
_success_after_failures = 2  # 在 N 次失败后成功


def mock_tool_node(state: ErrorCountState) -> dict[str, Any]:
    """
    模拟工具节点

    模拟可能失败的工具调用，用于演示错误处理机制。

    注意：此处使用全局变量模拟失败场景，仅用于演示。
    生产环境应处理真实的 API 调用异常。
    """
    global _failure_count

    _failure_count += 1

    # 模拟：前几次失败，之后成功
    if _failure_count <= _success_after_failures:
        raise RuntimeError(f"模拟 API 调用失败 (第 {_failure_count} 次)")

    # 成功情况
    result = f"工具调用成功：处理查询 '{state.query}'"
    return {
        "result": result,
        "messages": [f"[工具] {result}"],
    }


# ==================== 错误处理节点 ====================


def error_count_node(state: ErrorCountState) -> dict[str, Any]:
    """
    错误计数节点

    记录错误并决定是否触发熔断。
    """
    new_error_count = state.error_count + 1
    circuit_open = new_error_count >= state.max_errors
    retry_flag = not circuit_open

    return {
        "error_count": new_error_count,
        "circuit_open": circuit_open,
        "retry_flag": retry_flag,
        "messages": [
            f"[错误计数] 第 {new_error_count} 次错误，"
            f"{'熔断触发' if circuit_open else '允许重试'}"
        ],
    }


# ==================== 熔断检查函数 ====================


def circuit_breaker_check(
    state: ErrorCountState,
) -> Literal["mock_tool_node", "fallback_node"]:
    """
    熔断检查函数

    根据熔断状态决定执行路径。

    Returns:
        目标节点名称
    """
    if state.circuit_open:
        return "fallback_node"
    return "mock_tool_node"


# ==================== 降级处理节点 ====================


def fallback_node(state: ErrorCountState) -> dict[str, Any]:
    """
    降级处理节点

    当熔断触发时提供友好的降级响应。
    """
    result = (
        f"抱歉，服务暂时不可用。您的查询 '{state.query}' 无法处理。\n"
        f"请稍后重试或联系管理员。\n"
        f"错误次数：{state.error_count}"
    )

    return {
        "result": result,
        "messages": ["[降级] 熔断已触发，执行降级处理"],
    }


# ==================== 工作流构建 ====================


class ErrorHandlerWorkflow:
    """错误处理工作流"""

    def __init__(self) -> None:
        """初始化工作流"""
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(ErrorCountState)

        # 添加节点
        workflow.add_node("mock_tool_node", self._wrap_tool_node)
        workflow.add_node("error_count_node", error_count_node)
        workflow.add_node("fallback_node", fallback_node)

        # 设置入口点
        workflow.set_entry_point("mock_tool_node")

        # 条件边 - 根据熔断状态决定路径
        workflow.add_conditional_edges(
            "error_count_node",
            self._route_after_error,
            {
                "retry": "mock_tool_node",
                "end": END,
            },
        )

        # 降级节点连接到结束
        workflow.add_edge("fallback_node", END)

        return workflow.compile()

    def _wrap_tool_node(self, state: ErrorCountState) -> dict[str, Any]:
        """
        包装工具节点

        捕获异常并返回错误状态。
        """
        try:
            return mock_tool_node(state)
        except Exception as e:
            # 返回错误状态，触发错误计数节点
            return {
                "result": "",
                "messages": [f"[工具异常] {str(e)}"],
            }

    def _route_after_error(self, state: ErrorCountState) -> Literal["retry", "end"]:
        """
        错误后的路由决策

        根据错误计数和熔断状态决定是否重试。
        """
        if state.circuit_open:
            return "end"

        # 检查上一次操作是否成功（通过检查 result 是否为空）
        if state.result and "成功" in state.result:
            return "end"

        return "retry"

    def run(self, query: str) -> dict[str, Any]:
        """
        执行工作流

        Args:
            query: 用户查询

        Returns:
            最终状态
        """
        initial_state = ErrorCountState(query=query)
        return self.app.invoke(initial_state)

    def reset_failure_count(self) -> None:
        """重置失败计数（用于测试）"""
        global _failure_count
        _failure_count = 0


# ==================== 增强版工作流（带前置熔断检查）====================


class CircuitBreakerWorkflow:
    """带前置熔断检查的工作流"""

    def __init__(self) -> None:
        """初始化工作流"""
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(ErrorCountState)

        # 添加节点
        workflow.add_node("entry_check", self._entry_check_node)
        workflow.add_node("mock_tool_node", self._wrap_tool_node)
        workflow.add_node("error_count_node", error_count_node)
        workflow.add_node("fallback_node", fallback_node)

        # 设置入口点
        workflow.set_entry_point("entry_check")

        # 入口检查 -> 条件路由
        workflow.add_conditional_edges(
            "entry_check",
            circuit_breaker_check,
            {
                "mock_tool_node": "mock_tool_node",
                "fallback_node": "fallback_node",
            },
        )

        # 工具节点成功 -> 结束
        # 工具节点失败 -> 错误计数
        workflow.add_conditional_edges(
            "mock_tool_node",
            self._check_tool_result,
            {
                "success": END,
                "error": "error_count_node",
            },
        )

        # 错误计数 -> 条件路由
        workflow.add_conditional_edges(
            "error_count_node",
            self._route_after_error_count,
            {
                "retry": "entry_check",
                "fallback": "fallback_node",
            },
        )

        # 降级节点连接到结束
        workflow.add_edge("fallback_node", END)

        return workflow.compile()

    def _entry_check_node(self, state: ErrorCountState) -> dict[str, Any]:
        """入口检查节点（用于重置状态）"""
        return {"messages": ["[入口] 开始处理请求"]}

    def _wrap_tool_node(self, state: ErrorCountState) -> dict[str, Any]:
        """包装工具节点"""
        global _failure_count
        _failure_count += 1

        try:
            if _failure_count <= _success_after_failures:
                raise RuntimeError(f"模拟 API 调用失败 (第 {_failure_count} 次)")

            result = f"工具调用成功：处理查询 '{state.query}'"
            return {
                "result": result,
                "messages": [f"[工具] {result}"],
            }
        except Exception as e:
            return {
                "result": "",
                "messages": [f"[工具异常] {str(e)}"],
            }

    def _check_tool_result(self, state: ErrorCountState) -> Literal["success", "error"]:
        """检查工具执行结果"""
        if state.result and "成功" in state.result:
            return "success"
        return "error"

    def _route_after_error_count(
        self, state: ErrorCountState
    ) -> Literal["retry", "fallback"]:
        """错误计数后路由"""
        if state.circuit_open:
            return "fallback"
        return "retry"

    def run(self, query: str) -> dict[str, Any]:
        """执行工作流"""
        initial_state = ErrorCountState(query=query)
        return self.app.invoke(initial_state)

    def reset(self) -> None:
        """重置状态（用于测试）"""
        global _failure_count
        _failure_count = 0


# ==================== 演示函数 ====================


def demo_error_handler() -> None:
    """演示错误处理工作流"""
    print("=== 错误处理工作流示例 ===\n")

    # 重置失败计数
    global _failure_count
    _failure_count = 0

    workflow = ErrorHandlerWorkflow()

    print("模拟多次调用，观察错误处理和熔断机制：\n")

    for i in range(4):
        print(f"第 {i + 1} 次调用：")
        print("-" * 40)

        result = workflow.run("测试查询")
        print(f"错误计数：{result['error_count']}")
        print(f"熔断状态：{'已触发' if result['circuit_open'] else '未触发'}")
        print(f"结果：{result['result'] or '（无结果）'}")

        # 检查是否触发了熔断
        if result["circuit_open"]:
            print("\n熔断已触发，停止后续调用")
            break
        print()


def demo_circuit_breaker() -> None:
    """演示熔断机制"""
    print("\n=== 熔断机制示例 ===\n")

    # 重置
    global _failure_count
    _failure_count = 0

    workflow = CircuitBreakerWorkflow()

    print("带前置熔断检查的工作流：\n")

    result = workflow.run("测试熔断")
    print(f"最终错误计数：{result['error_count']}")
    print(f"熔断状态：{'已触发' if result['circuit_open'] else '未触发'}")
    print(f"结果：{result['result'] or '（降级响应）'}")


if __name__ == "__main__":
    demo_error_handler()
    demo_circuit_breaker()
