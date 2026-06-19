"""
意图路由工作流单元测试

测试 intent_router_demo 模块的所有功能。
"""

import pytest

from demo.examples.langgraph_workflows.intent_router_demo import (
    AgentState,
    IntentRouterWorkflow,
    error_handler,
    intent_node,
    rag_node,
    route_logic,
    tool_node,
)


class TestAgentState:
    """测试 AgentState 状态模型"""

    def test_state_initialization(self) -> None:
        """测试状态初始化"""
        state = AgentState(query="测试查询")
        assert state.query == "测试查询"
        assert state.intent == ""
        assert state.result == ""
        assert state.error_count == 0
        assert state.retry_flag is False
        assert state.messages == []

    def test_state_with_intent(self) -> None:
        """测试带意图的状态"""
        state = AgentState(query="天气", intent="weather")
        assert state.intent == "weather"


class TestIntentNode:
    """测试意图识别节点"""

    def test_weather_intent(self) -> None:
        """测试天气意图识别"""
        state = AgentState(query="今天天气怎么样？")
        result = intent_node(state)
        assert result["intent"] == "weather"

    def test_weather_intent_english(self) -> None:
        """测试英文天气意图"""
        state = AgentState(query="What's the weather today?")
        result = intent_node(state)
        assert result["intent"] == "weather"

    def test_knowledge_intent(self) -> None:
        """测试知识检索意图"""
        state = AgentState(query="什么是人工智能？")
        result = intent_node(state)
        assert result["intent"] == "knowledge"

    def test_how_to_intent(self) -> None:
        """测试如何类问题意图"""
        state = AgentState(query="如何学习编程？")
        result = intent_node(state)
        assert result["intent"] == "knowledge"

    def test_unknown_intent(self) -> None:
        """测试未知意图"""
        state = AgentState(query="随便说说")
        result = intent_node(state)
        assert result["intent"] == "unknown"

    def test_temperature_intent(self) -> None:
        """测试温度相关意图"""
        state = AgentState(query="今天气温多少？")
        result = intent_node(state)
        assert result["intent"] == "weather"


class TestRouteLogic:
    """测试条件路由函数"""

    def test_route_to_tool_node(self) -> None:
        """测试路由到工具节点"""
        state = AgentState(intent="weather")
        result = route_logic(state)
        assert result == "tool_node"

    def test_route_to_rag_node(self) -> None:
        """测试路由到 RAG 节点"""
        state = AgentState(intent="knowledge")
        result = route_logic(state)
        assert result == "rag_node"

    def test_route_to_error_handler(self) -> None:
        """测试路由到错误处理节点"""
        state = AgentState(intent="unknown")
        result = route_logic(state)
        assert result == "error_handler"


class TestProcessingNodes:
    """测试处理节点"""

    def test_rag_node(self) -> None:
        """测试 RAG 检索节点"""
        state = AgentState(query="什么是机器学习？")
        result = rag_node(state)
        assert "RAG" in result["result"]
        assert len(result["messages"]) > 0

    def test_tool_node(self) -> None:
        """测试工具调用节点"""
        state = AgentState(query="天气查询")
        result = tool_node(state)
        assert "天气" in result["result"]
        assert len(result["messages"]) > 0

    def test_error_handler(self) -> None:
        """测试错误处理节点"""
        state = AgentState(query="无效查询")
        result = error_handler(state)
        assert "抱歉" in result["result"]
        assert result["error_count"] == 1


class TestIntentRouterWorkflow:
    """测试意图路由工作流"""

    @pytest.fixture
    def workflow(self) -> IntentRouterWorkflow:
        """创建工作流实例"""
        return IntentRouterWorkflow()

    def test_workflow_creation(self, workflow: IntentRouterWorkflow) -> None:
        """测试工作流创建"""
        assert workflow.app is not None

    def test_weather_query(self, workflow: IntentRouterWorkflow) -> None:
        """测试天气查询"""
        result = workflow.run("今天天气怎么样？")
        assert result["intent"] == "weather"
        assert "天气" in result["result"]

    def test_knowledge_query(self, workflow: IntentRouterWorkflow) -> None:
        """测试知识查询"""
        result = workflow.run("什么是人工智能？")
        assert result["intent"] == "knowledge"
        assert "RAG" in result["result"]

    def test_unknown_query(self, workflow: IntentRouterWorkflow) -> None:
        """测试未知查询"""
        result = workflow.run("随机输入")
        assert result["intent"] == "unknown"
        assert "抱歉" in result["result"]

    def test_workflow_state_persistence(self, workflow: IntentRouterWorkflow) -> None:
        """测试状态持久化"""
        result = workflow.run("今天天气怎么样")
        # 工作流执行成功，结果包含正确的意图和处理信息
        assert result["intent"] == "weather"
        assert "天气" in result["result"]


class TestEdgeCases:
    """边界条件测试"""

    @pytest.fixture
    def workflow(self) -> IntentRouterWorkflow:
        """创建工作流实例"""
        return IntentRouterWorkflow()

    def test_empty_query(self, workflow: IntentRouterWorkflow) -> None:
        """测试空查询"""
        result = workflow.run("")
        assert result["intent"] == "unknown"

    def test_long_query(self, workflow: IntentRouterWorkflow) -> None:
        """测试超长查询"""
        long_query = "天气" * 1000
        result = workflow.run(long_query)
        assert result["intent"] == "weather"

    def test_special_characters(self, workflow: IntentRouterWorkflow) -> None:
        """测试特殊字符"""
        result = workflow.run("什么是 @#$% ？")
        assert result["intent"] in ["knowledge", "unknown"]

    def test_mixed_language(self, workflow: IntentRouterWorkflow) -> None:
        """测试中英混合"""
        result = workflow.run("今天weather怎么样？")
        assert result["intent"] == "weather"
