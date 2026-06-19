"""
意图识别与条件路由工作流示例

演示如何使用 LangGraph 构建智能问答助手的意图识别与路由系统。
包括：意图识别节点、条件路由、RAG 检索节点、工具调用节点、错误处理。

Day 5 讲义：AI 智能体应用实战 - 工作流深化设计
"""

from typing import Annotated, Any, Literal

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

# ==================== 状态定义 ====================


class AgentState(BaseModel):
    """
    智能体状态

    包含查询、意图识别结果、处理结果、错误计数和重试标志。
    """

    # 用户输入
    query: str = ""

    # 意图识别结果
    intent: str = ""

    # 处理结果
    result: str = ""

    # 错误计数（用于熔断机制）
    error_count: int = 0

    # 重试标志
    retry_flag: bool = False

    # 消息历史
    messages: Annotated[list[str], "消息列表"] = []


# ==================== 意图识别节点 ====================


def intent_node(state: AgentState) -> dict[str, Any]:
    """
    意图识别节点

    分析用户查询，识别意图类型：
    - weather: 天气查询
    - knowledge: 知识检索
    - unknown: 未知意图

    Args:
        state: 当前状态

    Returns:
        状态更新
    """
    query_lower = state.query.lower()

    # 模拟意图识别逻辑（生产环境应使用 LLM）
    if any(kw in query_lower for kw in ["天气", "weather", "温度", "气温"]):
        intent = "weather"
    elif any(kw in query_lower for kw in ["什么是", "如何", "为什么", "解释"]):
        intent = "knowledge"
    else:
        intent = "unknown"

    return {
        "intent": intent,
        "messages": [f"[意图识别] 识别为 '{intent}' 类型"],
    }


# ==================== 处理节点 ====================


def rag_node(state: AgentState) -> dict[str, Any]:
    """
    RAG 检索节点

    模拟知识库检索过程。

    注意：此处为 Mock 实现，生产环境应连接真实向量数据库。
    """
    # 模拟检索结果
    mock_results = {
        "什么是": "知识检索结果：这是一个概念性的问题，答案是...",
        "如何": "知识检索结果：操作步骤如下...",
        "为什么": "知识检索结果：原因是...",
    }

    # 简单匹配模拟
    result = mock_results.get(
        state.query[:2], f"RAG 检索结果：关于 '{state.query}' 的知识..."
    )

    return {
        "result": result,
        "messages": [f"[RAG] {result}"],
    }


def tool_node(state: AgentState) -> dict[str, Any]:
    """
    工具调用节点

    模拟天气 API 调用。

    注意：此处为 Mock 实现，生产环境应调用真实天气 API。
    """
    # 模拟天气 API 响应
    result = "天气查询结果：当前温度 25°C，晴天"

    return {
        "result": result,
        "messages": [f"[天气工具] {result}"],
    }


def error_handler(state: AgentState) -> dict[str, Any]:
    """
    错误处理节点

    处理未知意图或错误情况。
    """
    result = f"抱歉，我无法理解您的问题 '{state.query}'。请尝试换一种方式提问。"

    return {
        "result": result,
        "error_count": state.error_count + 1,
        "messages": [f"[错误处理] {result}"],
    }


# ==================== 条件路由函数 ====================


def route_logic(state: AgentState) -> Literal["tool_node", "rag_node", "error_handler"]:
    """
    条件路由函数

    根据意图识别结果决定下一个执行节点。

    Returns:
        目标节点名称
    """
    if state.intent == "weather":
        return "tool_node"
    elif state.intent == "knowledge":
        return "rag_node"
    else:
        return "error_handler"


# ==================== 工作流构建 ====================


class IntentRouterWorkflow:
    """意图路由工作流"""

    def __init__(self) -> None:
        """初始化工作流"""
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("intent_node", intent_node)
        workflow.add_node("rag_node", rag_node)
        workflow.add_node("tool_node", tool_node)
        workflow.add_node("error_handler", error_handler)

        # 设置入口点
        workflow.set_entry_point("intent_node")

        # 添加条件边 - 根据意图路由
        workflow.add_conditional_edges(
            "intent_node",
            route_logic,
            {
                "tool_node": "tool_node",
                "rag_node": "rag_node",
                "error_handler": "error_handler",
            },
        )

        # 所有处理节点连接到结束
        workflow.add_edge("rag_node", END)
        workflow.add_edge("tool_node", END)
        workflow.add_edge("error_handler", END)

        return workflow.compile()

    def run(self, query: str) -> dict[str, Any]:
        """
        执行工作流

        Args:
            query: 用户查询

        Returns:
            最终状态
        """
        initial_state = AgentState(query=query)
        return self.app.invoke(initial_state)


# ==================== 演示函数 ====================


def demo_intent_router() -> None:
    """演示意图路由工作流"""
    print("=== 意图路由工作流示例 ===\n")

    workflow = IntentRouterWorkflow()

    # 测试不同类型的查询
    test_queries = [
        "今天北京天气怎么样？",
        "什么是人工智能？",
        "随便聊聊",
    ]

    for query in test_queries:
        print(f"查询：{query}")
        print("-" * 40)

        result = workflow.run(query)

        print(f"意图：{result['intent']}")
        print(f"结果：{result['result']}")
        print(f"消息数：{len(result['messages'])}")
        print()


def demo_stream_execution() -> None:
    """演示流式执行"""
    print("=== 流式执行示例 ===\n")

    workflow = IntentRouterWorkflow()
    initial_state = AgentState(query="今天天气如何？")

    print("流式执行过程：\n")

    for event in workflow.app.stream(initial_state):
        for node_name, node_output in event.items():
            print(f"节点 '{node_name}'：")
            if node_output.get("messages"):
                print(f"  最新消息: {node_output['messages'][-1]}")
            print()


if __name__ == "__main__":
    demo_intent_router()
    demo_stream_execution()
