"""
条件路由示例

演示如何使用 LangGraph 的条件边实现动态路由。
根据状态值决定执行路径，支持分支和循环。

Day 3 讲义：AI 智能体应用实战 - LangGraph 工作流
"""

from typing import Annotated, Any, Literal

from langgraph.graph import END, StateGraph
from pydantic import BaseModel


# ==================== 状态定义 ====================


class RoutingState(BaseModel):
    """路由状态"""

    # 输入
    user_input: str = ""

    # 分类结果
    category: str = ""

    # 处理结果
    response: str = ""

    # 重试计数
    retry_count: int = 0

    # 是否需要重试
    needs_retry: bool = False

    # 消息历史
    messages: Annotated[list[str], "消息列表"] = []


# ==================== 节点函数 ====================


def classify_node(state: RoutingState) -> dict[str, Any]:
    """
    分类节点

    分析用户输入并进行分类。
    """
    # 模拟分类逻辑
    input_lower = state.user_input.lower()

    if "天气" in input_lower or "weather" in input_lower:
        category = "weather"
    elif "新闻" in input_lower or "news" in input_lower:
        category = "news"
    elif "计算" in input_lower or "calculate" in input_lower:
        category = "calculator"
    else:
        category = "general"

    return {
        "category": category,
        "messages": [f"[分类] 识别为 '{category}' 类型"],
    }


def weather_handler(state: RoutingState) -> dict[str, Any]:
    """天气处理器"""
    response = f"天气预报：今天晴朗，气温 25°C"
    return {
        "response": response,
        "messages": [f"[天气] {response}"],
    }


def news_handler(state: RoutingState) -> dict[str, Any]:
    """新闻处理器"""
    response = "今日头条：AI 技术持续发展，各行业加速数字化转型"
    return {
        "response": response,
        "messages": [f"[新闻] {response}"],
    }


def calculator_handler(state: RoutingState) -> dict[str, Any]:
    """计算器处理器"""
    # 简单的计算模拟
    response = "计算结果：42（生命、宇宙及一切的终极答案）"
    return {
        "response": response,
        "messages": [f"[计算] {response}"],
    }


def general_handler(state: RoutingState) -> dict[str, Any]:
    """通用处理器"""
    response = f"收到您的请求：'{state.user_input}'，正在处理中..."
    return {
        "response": response,
        "messages": [f"[通用] {response}"],
    }


def validate_response(state: RoutingState) -> dict[str, Any]:
    """
    验证响应

    检查响应是否有效，决定是否需要重试。
    """
    # 模拟验证逻辑：如果响应为空或太短，需要重试
    if not state.response or len(state.response) < 5:
        needs_retry = state.retry_count < 3
        return {
            "needs_retry": needs_retry,
            "retry_count": state.retry_count + 1,
            "messages": [
                f"[验证] 响应无效，{'重试中...' if needs_retry else '达到最大重试次数'}"
            ],
        }

    return {
        "needs_retry": False,
        "messages": [f"[验证] 响应有效"],
    }


# ==================== 路由函数 ====================


def route_by_category(
    state: RoutingState,
) -> Literal["weather", "news", "calculator", "general"]:
    """
    根据分类结果路由

    这是条件边的路由函数，返回下一个要执行的节点名称。
    """
    return state.category  # type: ignore


def route_by_validation(state: RoutingState) -> Literal["classify", END]:
    """
    根据验证结果路由

    决定是重试还是结束。
    """
    if state.needs_retry:
        return "classify"  # 重新分类
    return END  # 结束


# ==================== 图构建 ====================


class RoutingGraph:
    """条件路由图"""

    def __init__(self) -> None:
        """初始化路由图"""
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(RoutingState)

        # 添加节点
        workflow.add_node("classify", classify_node)
        workflow.add_node("weather", weather_handler)
        workflow.add_node("news", news_handler)
        workflow.add_node("calculator", calculator_handler)
        workflow.add_node("general", general_handler)
        workflow.add_node("validate", validate_response)

        # 设置入口点
        workflow.set_entry_point("classify")

        # 添加条件边 - 根据分类路由到不同处理器
        workflow.add_conditional_edges(
            "classify",
            route_by_category,
            {
                "weather": "weather",
                "news": "news",
                "calculator": "calculator",
                "general": "general",
            },
        )

        # 所有处理器都连接到验证节点
        for handler in ["weather", "news", "calculator", "general"]:
            workflow.add_edge(handler, "validate")

        # 添加条件边 - 根据验证结果决定是否重试
        workflow.add_conditional_edges(
            "validate",
            route_by_validation,
            {
                "classify": "classify",
                END: END,
            },
        )

        return workflow.compile()

    def run(self, user_input: str) -> dict[str, Any]:
        """
        执行工作流

        Args:
            user_input: 用户输入

        Returns:
            最终状态
        """
        initial_state = RoutingState(user_input=user_input)
        return self.app.invoke(initial_state)


# ==================== 演示函数 ====================


def demo_conditional_routing() -> None:
    """演示条件路由"""
    print("=== 条件路由示例 ===\n")

    graph = RoutingGraph()

    # 测试不同类型的输入
    test_inputs = [
        "今天天气怎么样？",
        "有什么新闻？",
        "帮我计算一下",
        "随便聊聊",
    ]

    for user_input in test_inputs:
        print(f"\n输入：{user_input}")
        print("-" * 40)

        result = graph.run(user_input)

        print(f"分类：{result['category']}")
        print(f"响应：{result['response']}")
        print(f"消息数：{len(result['messages'])}")


def demo_loop_routing() -> None:
    """演示循环路由"""
    print("\n=== 循环路由示例 ===\n")

    # 构建一个带循环的简单图
    class CounterState(BaseModel):
        count: int = 0
        max_count: int = 3
        messages: list[str] = []

    def increment(state: CounterState) -> dict[str, Any]:
        return {
            "count": state.count + 1,
            "messages": [f"计数: {state.count + 1}"],
        }

    def check_continue(state: CounterState) -> Literal["increment", END]:
        if state.count < state.max_count:
            return "increment"
        return END

    workflow = StateGraph(CounterState)
    workflow.add_node("increment", increment)
    workflow.set_entry_point("increment")
    workflow.add_conditional_edges(
        "increment",
        check_continue,
        {"increment": "increment", END: END},
    )

    app = workflow.compile()

    # 执行
    result = app.invoke(CounterState())
    print(f"最终计数: {result['count']}")
    print(f"消息: {result['messages']}")


if __name__ == "__main__":
    demo_conditional_routing()
    demo_loop_routing()
