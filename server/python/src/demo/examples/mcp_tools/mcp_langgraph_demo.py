"""
MCP 与 LangGraph 集成示例

演示如何在 LangGraph 工作流中使用 MCP 工具。
构建一个能够调用 MCP 工具的智能体工作流。

Day 3 讲义：AI 智能体应用实战 - MCP 工具集成
"""

from typing import Annotated, Any, Literal

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

# ==================== 状态定义 ====================


class AgentState(BaseModel):
    """智能体状态"""

    # 用户请求
    user_request: str = ""

    # 决策
    action: str = ""

    # 工具名称
    tool_name: str = ""

    # 工具参数
    tool_args: dict[str, Any] = {}

    # 工具结果
    tool_result: str = ""

    # 最终回复
    response: str = ""

    # 是否需要继续
    should_continue: bool = True

    # 消息历史
    messages: Annotated[list[str], "消息列表"] = []

    # 迭代次数
    iterations: int = 0


# ==================== 模拟 MCP 工具执行器 ====================


def execute_mcp_tool(tool_name: str, args: dict[str, Any]) -> str:
    """
    执行 MCP 工具（模拟）

    Args:
        tool_name: 工具名称
        args: 工具参数

    Returns:
        执行结果
    """
    # 模拟工具执行
    tool_responses = {
        "mcp_search": f"搜索结果：找到 3 条关于 '{args.get('query', '')}' 的记录",
        "mcp_weather": f"天气查询：{args.get('city', '未知')} 晴朗，25°C",
        "mcp_file": f"文件读取：成功读取 {args.get('path', '未知文件')}",
        "mcp_db": f"数据库查询：返回 {args.get('limit', 10)} 条记录",
    }

    return tool_responses.get(tool_name, f"[{tool_name}] 执行完成，参数：{args}")


# ==================== 节点函数 ====================


def analyze_request(state: AgentState) -> dict[str, Any]:
    """
    分析请求节点

    理解用户意图并决定下一步行动。
    """
    request = state.user_request.lower()

    # 简单的意图识别
    if "天气" in request or "weather" in request:
        action = "call_tool"
        tool_name = "mcp_weather"
        tool_args = {"city": "北京"}  # 模拟提取的城市
    elif "搜索" in request or "search" in request:
        action = "call_tool"
        tool_name = "mcp_search"
        tool_args = {"query": "LangChain"}  # 模拟提取的关键词
    elif "文件" in request or "file" in request:
        action = "call_tool"
        tool_name = "mcp_file"
        tool_args = {"path": "/data/test.txt"}  # 模拟提取的路径
    else:
        action = "respond_directly"
        tool_name = ""
        tool_args = {}

    return {
        "action": action,
        "tool_name": tool_name,
        "tool_args": tool_args,
        "iterations": state.iterations + 1,
        "messages": [f"[分析] 意图: {action}, 工具: {tool_name or '无'}"],
    }


def call_mcp_tool(state: AgentState) -> dict[str, Any]:
    """
    调用 MCP 工具节点
    """
    result = execute_mcp_tool(state.tool_name, state.tool_args)

    return {
        "tool_result": result,
        "messages": [f"[工具] {result}"],
    }


def generate_response(state: AgentState) -> dict[str, Any]:
    """
    生成响应节点

    根据工具结果或直接生成回复。
    """
    if state.tool_result:
        response = f"根据查询结果：{state.tool_result}"
    else:
        response = f"收到您的请求：{state.user_request}"

    return {
        "response": response,
        "should_continue": False,
        "messages": [f"[回复] {response}"],
    }


def should_continue(state: AgentState) -> Literal["analyze", END]:
    """
    路由函数

    决定是否继续迭代。
    """
    # 限制最大迭代次数
    if state.iterations >= 5:
        return END

    if state.should_continue and state.action == "call_tool":
        # 如果需要继续且有工具调用，回到分析阶段
        return END  # 简化：一次工具调用后结束

    return END


def route_action(state: AgentState) -> Literal["call_tool", "generate_response"]:
    """
    根据动作路由
    """
    if state.action == "call_tool":
        return "call_tool"
    return "generate_response"


# ==================== 图构建 ====================


class MCPAgentGraph:
    """
    MCP 智能体图

    集成 MCP 工具的 LangGraph 智能体。
    """

    def __init__(self) -> None:
        """初始化智能体图"""
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("analyze", analyze_request)
        workflow.add_node("call_tool", call_mcp_tool)
        workflow.add_node("generate_response", generate_response)

        # 设置入口点
        workflow.set_entry_point("analyze")

        # 条件路由 - 根据动作决定下一步
        workflow.add_conditional_edges(
            "analyze",
            route_action,
            {
                "call_tool": "call_tool",
                "generate_response": "generate_response",
            },
        )

        # 工具调用后生成响应
        workflow.add_edge("call_tool", "generate_response")

        # 结束
        workflow.add_edge("generate_response", END)

        return workflow.compile()

    def run(self, user_request: str) -> dict[str, Any]:
        """
        执行智能体

        Args:
            user_request: 用户请求

        Returns:
            最终状态
        """
        initial_state = AgentState(user_request=user_request)
        return self.app.invoke(initial_state)


# ==================== ReAct 风格智能体 ====================


class ReActAgentGraph:
    """
    ReAct 风格智能体

    实现 Reasoning (推理) + Acting (行动) 循环。
    """

    def __init__(self, max_iterations: int = 3) -> None:
        """
        初始化 ReAct 智能体

        Args:
            max_iterations: 最大迭代次数
        """
        self.max_iterations = max_iterations
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建 ReAct 图"""
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("think", self._think_node)
        workflow.add_node("act", self._act_node)

        # 设置入口点
        workflow.set_entry_point("think")

        # 条件边
        workflow.add_conditional_edges(
            "think",
            self._should_act,
            {
                "act": "act",
                END: END,
            },
        )

        workflow.add_conditional_edges(
            "act",
            self._should_continue,
            {
                "think": "think",
                END: END,
            },
        )

        return workflow.compile()

    def _think_node(self, state: AgentState) -> dict[str, Any]:
        """思考节点"""
        # 模拟推理过程
        thought = f"思考：需要处理请求 '{state.user_request}'"
        return {
            "iterations": state.iterations + 1,
            "messages": [thought],
        }

    def _act_node(self, state: AgentState) -> dict[str, Any]:
        """行动节点"""
        # 简化：直接生成响应
        response = f"响应：已处理请求 '{state.user_request}'"
        return {
            "response": response,
            "should_continue": False,
            "messages": [response],
        }

    def _should_act(self, state: AgentState) -> Literal["act", END]:
        """是否需要行动"""
        if state.iterations >= self.max_iterations:
            return END
        return "act"

    def _should_continue(self, state: AgentState) -> Literal["think", END]:
        """是否继续"""
        if state.should_continue and state.iterations < self.max_iterations:
            return "think"
        return END

    def run(self, user_request: str) -> dict[str, Any]:
        """执行智能体"""
        initial_state = AgentState(user_request=user_request)
        return self.app.invoke(initial_state)


# ==================== 演示函数 ====================


def demo_mcp_agent() -> None:
    """演示 MCP 智能体"""
    print("=== MCP 智能体演示 ===\n")

    agent = MCPAgentGraph()

    # 测试不同类型的请求
    test_requests = [
        "今天天气怎么样？",
        "帮我搜索一下 LangChain",
        "读取一下配置文件",
        "随便聊聊天",
    ]

    for request in test_requests:
        print(f"\n请求：{request}")
        print("-" * 40)

        result = agent.run(request)

        print(f"动作：{result['action']}")
        print(f"工具：{result['tool_name'] or '无'}")
        print(f"响应：{result['response']}")

        print("\n消息历史：")
        for msg in result["messages"]:
            print(f"  {msg}")


def demo_react_agent() -> None:
    """演示 ReAct 智能体"""
    print("\n=== ReAct 智能体演示 ===\n")

    agent = ReActAgentGraph(max_iterations=2)

    result = agent.run("帮我分析一下项目状态")

    print(f"响应：{result['response']}")
    print(f"迭代次数：{result['iterations']}")

    print("\n执行过程：")
    for msg in result["messages"]:
        print(f"  {msg}")


if __name__ == "__main__":
    demo_mcp_agent()
    demo_react_agent()
