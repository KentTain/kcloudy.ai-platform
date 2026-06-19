"""
智能体核心逻辑示例单元测试

测试覆盖：
- 人设配置
- 知识库关联
- 工作流编排
- 完整智能体
"""


from demo.examples.agent_core.agent_demo import AgentDemo, SimpleAgent
from demo.examples.agent_core.knowledge_base_demo import (
    AgentKnowledgeBase,
    KnowledgeBaseDemo,
    MockRetriever,
)
from demo.examples.agent_core.persona_demo import (
    AgentPersona,
    PersonaConfig,
    PersonaDemo,
)
from demo.examples.agent_core.workflow_demo import AgentWorkflow


class TestPersonaConfig:
    """PersonaConfig 测试"""

    def test_init_default_values(self) -> None:
        """测试默认初始化"""
        config = PersonaConfig()
        assert config.role == "智能助手"
        assert config.tone == "友好、专业"

    def test_init_custom_values(self) -> None:
        """测试自定义初始化"""
        config = PersonaConfig(
            role="Python 专家",
            tone="专业、简洁",
        )
        assert config.role == "Python 专家"
        assert config.tone == "专业、简洁"

    def test_template_python_expert(self) -> None:
        """测试 Python 专家模板"""
        config = PersonaConfig(template_name="python_expert")
        assert config.role == "Python 编程专家"
        assert "Python" in config.system_prompt

    def test_template_code_reviewer(self) -> None:
        """测试代码审查专家模板"""
        config = PersonaConfig(template_name="code_reviewer")
        assert config.role == "代码审查专家"

    def test_system_prompt_generation(self) -> None:
        """测试系统提示词生成"""
        config = PersonaConfig(role="测试角色", tone="测试语气")
        prompt = config.system_prompt
        assert "测试角色" in prompt
        assert "测试语气" in prompt

    def test_to_dict_and_from_dict(self) -> None:
        """测试字典转换"""
        config = PersonaConfig(role="角色", tone="语气")
        data = config.to_dict()
        restored = PersonaConfig.from_dict(data)
        assert restored.role == config.role
        assert restored.tone == config.tone


class TestAgentPersona:
    """AgentPersona 测试"""

    def test_add_constraint(self) -> None:
        """测试添加约束"""
        config = PersonaConfig()
        persona = AgentPersona(config)
        persona.add_constraint("测试约束")
        prompt = persona.get_full_prompt()
        assert "测试约束" in prompt

    def test_set_output_format(self) -> None:
        """测试设置输出格式"""
        config = PersonaConfig()
        persona = AgentPersona(config)
        persona.set_output_format("格式: {content}")
        formatted = persona.format_response("内容")
        assert formatted == "格式: 内容"

    def test_format_response_default(self) -> None:
        """测试默认格式化"""
        config = PersonaConfig()
        persona = AgentPersona(config)
        formatted = persona.format_response("测试内容")
        assert "测试内容" in formatted


class TestPersonaDemo:
    """PersonaDemo 测试"""

    def test_create_and_get_persona(self) -> None:
        """测试创建和获取人设"""
        demo = PersonaDemo()
        persona = demo.create_persona("test", role="测试角色")
        assert demo.get_persona("test") == persona
        assert "test" in demo.list_personas()

    def test_get_nonexistent_persona(self) -> None:
        """测试获取不存在的人设"""
        demo = PersonaDemo()
        assert demo.get_persona("nonexistent") is None


class TestMockRetriever:
    """MockRetriever 测试"""

    def test_add_and_retrieve(self) -> None:
        """测试添加和检索"""
        retriever = MockRetriever()
        retriever.add_document("Python 是编程语言")
        results = retriever.retrieve("Python")
        assert len(results) > 0
        assert "Python" in results[0]["content"]

    def test_retrieve_with_score(self) -> None:
        """测试检索结果包含分数"""
        retriever = MockRetriever()
        retriever.add_document("Python 编程")
        retriever.add_document("Java 编程")
        results = retriever.retrieve("Python 编程")
        assert all("score" in r for r in results)

    def test_retrieve_top_k(self) -> None:
        """测试 Top-K 参数"""
        retriever = MockRetriever()
        for i in range(5):
            retriever.add_document(f"文档 {i}")
        results = retriever.retrieve("文档", top_k=2)
        assert len(results) <= 2


class TestAgentKnowledgeBase:
    """AgentKnowledgeBase 测试"""

    def test_add_documents(self) -> None:
        """测试添加文档"""
        kb = AgentKnowledgeBase()
        kb.add_documents(["文档1", "文档2"])
        result = kb.retrieve("文档")
        # 可能找不到（关键词匹配）
        assert isinstance(result, dict)

    def test_retrieve_structure(self) -> None:
        """测试检索结果结构"""
        kb = AgentKnowledgeBase()
        kb.add_documents(["Python 编程"])
        result = kb.retrieve("Python")
        assert "query" in result
        assert "results" in result
        assert "has_results" in result

    def test_get_context(self) -> None:
        """测试获取上下文"""
        kb = AgentKnowledgeBase()
        kb.add_documents(["Python 是编程语言"])
        context = kb.get_context("Python")
        assert isinstance(context, str)

    def test_build_prompt_with_context(self) -> None:
        """测试构建提示词"""
        kb = AgentKnowledgeBase()
        kb.add_documents(["Python 编程"])
        prompt = kb.build_prompt_with_context("什么是 Python", "你是助手")
        assert "什么是 Python" in prompt
        assert "你是助手" in prompt


class TestAgentWorkflow:
    """AgentWorkflow 测试"""

    def test_intent_recognition_tool(self) -> None:
        """测试工具意图识别"""
        workflow = AgentWorkflow()
        result = workflow.run("北京天气怎么样")
        assert result["intent"] == "tool"

    def test_intent_recognition_knowledge(self) -> None:
        """测试知识库意图识别"""
        workflow = AgentWorkflow()
        result = workflow.run("Python 如何定义函数")
        assert result["intent"] == "knowledge"

    def test_run_returns_response(self) -> None:
        """测试返回响应"""
        workflow = AgentWorkflow()
        result = workflow.run("测试问题")
        assert "response" in result
        assert result["response"]

    def test_messages_tracked(self) -> None:
        """测试消息追踪"""
        workflow = AgentWorkflow()
        result = workflow.run("测试")
        assert "messages" in result
        assert len(result["messages"]) > 0


class TestSimpleAgent:
    """SimpleAgent 测试"""

    def test_init(self) -> None:
        """测试初始化"""
        agent = SimpleAgent()
        assert agent.persona is not None
        assert agent.kb is not None

    def test_chat(self) -> None:
        """测试对话"""
        agent = SimpleAgent()
        result = agent.chat("测试问题")
        assert "response" in result
        assert "intent" in result

    def test_add_knowledge(self) -> None:
        """测试添加知识"""
        agent = SimpleAgent()
        agent.add_knowledge(["知识1", "知识2"])
        # 不抛出异常即可

    def test_history(self) -> None:
        """测试对话历史"""
        agent = SimpleAgent()
        agent.chat("问题1")
        agent.chat("问题2")
        history = agent.get_history()
        assert len(history) == 4  # 2 user + 2 assistant

    def test_clear_history(self) -> None:
        """测试清空历史"""
        agent = SimpleAgent()
        agent.chat("问题")
        agent.clear_history()
        assert len(agent.get_history()) == 0

    def test_get_system_prompt(self) -> None:
        """测试获取系统提示词"""
        agent = SimpleAgent()
        prompt = agent.get_system_prompt()
        assert prompt


class TestAgentDemo:
    """AgentDemo 测试"""

    def test_demo_instance(self) -> None:
        """测试演示实例化"""
        demo = AgentDemo()
        assert demo.agent is not None


class TestKnowledgeBaseDemo:
    """KnowledgeBaseDemo 测试"""

    def test_demo_instance(self) -> None:
        """测试演示实例化"""
        demo = KnowledgeBaseDemo()
        assert demo.kb is not None
