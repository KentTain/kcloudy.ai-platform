"""
LangGraph 工作流编排示例

演示使用 LangGraph 实现智能体工作流：
- 状态图节点定义
- 条件路由
- 检查点记忆

示例使用：
    workflow = AgentWorkflow()
    result = workflow.run("北京天气怎么样？")
"""

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    """智能体状态

    定义工作流中传递的状态数据。
    """

    query: str
    intent: str
    context: str
    tool_result: str
    response: str
    messages: list[dict[str, str]]


class AgentWorkflow:
    """智能体工作流

    使用 LangGraph StateGraph 实现完整的工作流：
    1. 意图识别
    2. 知识库检索 / 工具调用
    3. 响应生成
    """

    # 意图类型
    INTENT_KNOWLEDGE = "knowledge"
    INTENT_TOOL = "tool"
    INTENT_CHAT = "chat"

    # 关键词映射
    TOOL_KEYWORDS = {
        "天气": "weather",
        "weather": "weather",
    }

    def __init__(self) -> None:
        """初始化工作流"""
        self._build_graph()

    def _build_graph(self) -> None:
        """构建状态图"""
        # 创建状态图
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("intent_recognition", self._intent_node)
        workflow.add_node("knowledge_retrieval", self._knowledge_node)
        workflow.add_node("tool_call", self._tool_node)
        workflow.add_node("response_generation", self._response_node)

        # 设置入口
        workflow.set_entry_point("intent_recognition")

        # 添加条件路由
        workflow.add_conditional_edges(
            "intent_recognition",
            self._route_intent,
            {
                self.INTENT_KNOWLEDGE: "knowledge_retrieval",
                self.INTENT_TOOL: "tool_call",
                self.INTENT_CHAT: "response_generation",
            },
        )

        # 添加边
        workflow.add_edge("knowledge_retrieval", "response_generation")
        workflow.add_edge("tool_call", "response_generation")
        workflow.add_edge("response_generation", END)

        # 编译
        self.graph = workflow.compile()

    def _intent_node(self, state: AgentState) -> dict[str, Any]:
        """意图识别节点"""
        query = state["query"]

        # 检查是否包含工具关键词
        for keyword, tool_name in self.TOOL_KEYWORDS.items():
            if keyword in query.lower():
                return {
                    "intent": self.INTENT_TOOL,
                    "messages": [
                        *state.get("messages", []),
                        {
                            "role": "system",
                            "content": f"检测到工具调用意图: {tool_name}",
                        },
                    ],
                }

        # 默认为知识库检索
        return {
            "intent": self.INTENT_KNOWLEDGE,
            "messages": [
                *state.get("messages", []),
                {"role": "system", "content": "检测到知识库检索意图"},
            ],
        }

    def _knowledge_node(self, state: AgentState) -> dict[str, Any]:
        """知识库检索节点"""
        query = state["query"]

        # 模拟检索结果
        context = f"关于'{query}'的相关知识库内容..."

        return {
            "context": context,
            "messages": [
                *state.get("messages", []),
                {"role": "system", "content": f"检索到上下文: {context[:50]}..."},
            ],
        }

    def _tool_node(self, state: AgentState) -> dict[str, Any]:
        """工具调用节点"""
        query = state["query"]

        # 模拟工具调用
        tool_result = "工具调用结果: 北京天气晴朗，温度 25℃"

        return {
            "tool_result": tool_result,
            "messages": [
                *state.get("messages", []),
                {"role": "tool", "content": tool_result},
            ],
        }

    def _response_node(self, state: AgentState) -> dict[str, Any]:
        """响应生成节点"""
        intent = state["intent"]

        if intent == self.INTENT_TOOL:
            response = f"答案：{state['tool_result']}"
        elif intent == self.INTENT_KNOWLEDGE:
            response = f"答案：根据知识库，{state['context']}"
        else:
            response = f"答案：{state['query']}"

        return {
            "response": response,
            "messages": [
                *state.get("messages", []),
                {"role": "assistant", "content": response},
            ],
        }

    def _route_intent(self, state: AgentState) -> str:
        """路由函数"""
        return state["intent"]

    def run(self, query: str) -> dict[str, Any]:
        """运行工作流

        Args:
            query: 用户查询

        Returns:
            工作流结果
        """
        initial_state: AgentState = {
            "query": query,
            "intent": "",
            "context": "",
            "tool_result": "",
            "response": "",
            "messages": [],
        }

        result = self.graph.invoke(initial_state)
        return dict(result)

    def visualize(self) -> str:
        """返回工作流可视化描述"""
        return """
工作流结构：

[入口] → [意图识别] → [知识库检索] → [响应生成] → [结束]
                  ↘ [工具调用] ↗
"""


class WorkflowDemo:
    """工作流演示类"""

    def __init__(self) -> None:
        """初始化演示"""
        self.workflow = AgentWorkflow()

    def run_demo(self) -> None:
        """运行演示"""
        print("=" * 50)
        print("LangGraph 工作流编排示例")
        print("=" * 50)

        # 打印工作流结构
        print(self.workflow.visualize())

        # 测试查询
        queries = [
            "北京天气怎么样？",
            "Python 如何定义函数？",
        ]

        for query in queries:
            print(f"\n查询: {query}")
            print("-" * 30)

            result = self.workflow.run(query)

            print(f"意图: {result['intent']}")
            print(f"响应: {result['response']}")
            print(f"消息数: {len(result['messages'])}")


def demo() -> None:
    """演示工作流功能"""
    demo_instance = WorkflowDemo()
    demo_instance.run_demo()


if __name__ == "__main__":
    demo()
