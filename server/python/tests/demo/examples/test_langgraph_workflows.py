"""
LangGraph 工作流示例单元测试

测试 langgraph_workflows 模块的所有示例代码。
"""


from demo.examples.langgraph_workflows.conditional_routing_demo import (
    RoutingGraph,
    RoutingState,
)
from demo.examples.langgraph_workflows.memory_checkpoint_demo import (
    ConversationGraph,
    ConversationState,
)
from demo.examples.langgraph_workflows.state_graph_demo import (
    WorkflowState,
    create_simple_workflow,
)


class TestStateGraph:
    """测试 StateGraph 功能"""

    def test_create_workflow(self) -> None:
        """测试创建工作流"""
        app = create_simple_workflow()
        assert app is not None

    def test_workflow_execution(self) -> None:
        """测试工作流执行"""
        app = create_simple_workflow()

        initial_state = WorkflowState(query="测试查询")
        result = app.invoke(initial_state)

        assert result["current_step"] == "summarize"
        assert result["step_count"] >= 1  # 至少执行了步骤
        assert len(result["analysis"]) > 0
        assert len(result["result"]) > 0

    def test_workflow_state_mutation(self) -> None:
        """测试状态变更"""
        app = create_simple_workflow()

        initial_state = WorkflowState(query="测试")
        result = app.invoke(initial_state)

        # 验证状态被正确更新
        assert len(result["messages"]) >= 1  # 至少有一条消息
        assert result["step_count"] > 0

    def test_workflow_stream(self) -> None:
        """测试流式执行"""
        app = create_simple_workflow()

        initial_state = WorkflowState(query="流式测试")
        events = list(app.stream(initial_state))

        # 应该有多个事件
        assert len(events) >= 4

        # 检查事件顺序
        node_names = [list(event.keys())[0] for event in events]
        assert "analyze" in node_names
        assert "plan" in node_names
        assert "execute" in node_names
        assert "summarize" in node_names


class TestConditionalRouting:
    """测试条件路由"""

    def test_route_weather(self) -> None:
        """测试天气路由"""
        graph = RoutingGraph()

        result = graph.run("今天天气怎么样？")

        assert result["category"] == "weather"
        assert "天气" in result["response"]

    def test_route_news(self) -> None:
        """测试新闻路由"""
        graph = RoutingGraph()

        result = graph.run("有什么新闻？")

        assert result["category"] == "news"
        assert "头条" in result["response"]

    def test_route_calculator(self) -> None:
        """测试计算器路由"""
        graph = RoutingGraph()

        result = graph.run("帮我计算一下")

        assert result["category"] == "calculator"
        assert "计算结果" in result["response"]

    def test_route_general(self) -> None:
        """测试通用路由"""
        graph = RoutingGraph()

        result = graph.run("随便聊聊")

        assert result["category"] == "general"
        assert "收到" in result["response"]

    def test_routing_state_persistence(self) -> None:
        """测试路由状态持久化"""
        graph = RoutingGraph()

        result = graph.run("测试消息")

        # 检查消息历史
        assert len(result["messages"]) >= 1  # 至少有一条消息


class TestMemoryCheckpoint:
    """测试记忆与检查点"""

    def test_conversation_basic(self) -> None:
        """测试基本对话"""
        graph = ConversationGraph(enable_checkpointer=True)

        result = graph.chat("你好", thread_id="test-1")

        assert result["message_count"] == 1
        assert len(result["history"]) == 2  # 用户消息 + 助手回复

    def test_conversation_memory(self) -> None:
        """测试对话记忆"""
        graph = ConversationGraph(enable_checkpointer=True)
        thread_id = "memory-test"

        # 第一轮
        graph.chat("我是张三", thread_id=thread_id)

        # 第二轮 - 验证记忆
        result = graph.chat("我是谁？", thread_id=thread_id)

        assert result["user_name"] == "张三"
        assert result["message_count"] == 2

    def test_multiple_sessions(self) -> None:
        """测试多会话"""
        graph = ConversationGraph(enable_checkpointer=True)

        # 两个不同的会话
        result_a = graph.chat("会话A", thread_id="session-a")
        result_b = graph.chat("会话B", thread_id="session-b")

        # 消息计数应该各自独立
        assert result_a["message_count"] == 1
        assert result_b["message_count"] == 1

        # 获取各会话历史
        history_a = graph.get_history("session-a")
        history_b = graph.get_history("session-b")

        assert len(history_a) == 2
        assert len(history_b) == 2
        assert "会话A" in history_a[0]["content"]
        assert "会话B" in history_b[0]["content"]

    def test_get_state(self) -> None:
        """测试获取状态"""
        graph = ConversationGraph(enable_checkpointer=True)
        thread_id = "state-test"

        graph.chat("测试", thread_id=thread_id)

        state = graph.get_state(thread_id)
        assert state is not None
        assert state["message_count"] == 1

    def test_get_state_empty(self) -> None:
        """测试获取空状态"""
        graph = ConversationGraph(enable_checkpointer=True)

        state = graph.get_state("non-existent-thread")
        assert state is None

    def test_conversation_history(self) -> None:
        """测试对话历史"""
        graph = ConversationGraph(enable_checkpointer=True)
        thread_id = "history-test"

        # 多轮对话
        graph.chat("第一句", thread_id=thread_id)
        graph.chat("第二句", thread_id=thread_id)
        graph.chat("第三句", thread_id=thread_id)

        history = graph.get_history(thread_id)

        # 3轮对话 = 6条消息（用户+助手各3条）
        assert len(history) == 6

    def test_conversation_without_checkpointer(self) -> None:
        """测试不带检查点的对话"""
        graph = ConversationGraph(enable_checkpointer=False)

        result = graph.chat("测试", thread_id="no-checkpoint")

        # 应该正常执行
        assert result["message_count"] == 1


class TestStateModels:
    """测试状态模型"""

    def test_workflow_state_model(self) -> None:
        """测试工作流状态模型"""
        state = WorkflowState(query="测试")
        assert state.query == "测试"
        assert state.current_step == "start"
        assert state.step_count == 0
        assert state.messages == []

    def test_routing_state_model(self) -> None:
        """测试路由状态模型"""
        state = RoutingState(user_input="测试输入")
        assert state.user_input == "测试输入"
        assert state.category == ""
        assert state.retry_count == 0

    def test_conversation_state_model(self) -> None:
        """测试对话状态模型"""
        state = ConversationState(current_message="你好")
        assert state.current_message == "你好"
        assert state.history == []
        assert state.message_count == 0

    def test_state_serialization(self) -> None:
        """测试状态序列化"""
        state = WorkflowState(query="测试")
        state_dict = state.model_dump()

        assert "query" in state_dict
        assert "current_step" in state_dict
        assert "step_count" in state_dict
