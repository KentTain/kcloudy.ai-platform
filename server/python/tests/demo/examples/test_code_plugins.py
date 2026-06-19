"""
代码插件示例单元测试

测试覆盖：
- 代码问答插件
- 关键词匹配插件
- 插件与 LangGraph 集成
"""


from demo.examples.code_plugins.code_qa_plugin_demo import (
    CodeQADemo,
    CodeQAPlugin,
    PythonCodeQA,
)
from demo.examples.code_plugins.keyword_match_demo import (
    KeywordMatchDemo,
    KeywordMatchPlugin,
    MatchRule,
)
from demo.examples.code_plugins.plugin_integration_demo import (
    PluginIntegrationDemo,
    PluginRegistry,
    ToolNode,
)


class TestCodeQAPlugin:
    """CodeQAPlugin 测试"""

    def test_add_rule(self) -> None:
        """测试添加规则"""
        plugin = CodeQAPlugin()
        plugin.add_rule("test", "test answer")
        assert "test" in plugin.list_keywords()

    def test_query_match(self) -> None:
        """测试匹配查询"""
        plugin = CodeQAPlugin()
        plugin.add_rule("函数", "def example(): pass")
        result = plugin.query("Python 函数示例")
        assert "def" in result

    def test_query_no_match(self) -> None:
        """测试无匹配查询"""
        plugin = CodeQAPlugin()
        result = plugin.query("未知主题")
        assert result == "未找到相关代码"

    def test_list_keywords(self) -> None:
        """测试列出关键词"""
        plugin = CodeQAPlugin()
        plugin.add_rule("a", "1")
        plugin.add_rule("b", "2")
        keywords = plugin.list_keywords()
        assert "a" in keywords
        assert "b" in keywords


class TestPythonCodeQA:
    """PythonCodeQA 测试"""

    def test_init_with_preset_rules(self) -> None:
        """测试初始化包含预设规则"""
        plugin = PythonCodeQA()
        keywords = plugin.list_keywords()
        assert "函数" in keywords
        assert "类" in keywords

    def test_query_function(self) -> None:
        """测试函数查询"""
        plugin = PythonCodeQA()
        result = plugin.query("如何定义函数？")
        assert "def" in result

    def test_query_class(self) -> None:
        """测试类查询"""
        plugin = PythonCodeQA()
        result = plugin.query("如何定义类？")
        assert "class" in result

    def test_query_list(self) -> None:
        """测试列表查询"""
        plugin = PythonCodeQA()
        result = plugin.query("列表操作")
        assert "列表" in result


class TestCodeQADemo:
    """CodeQADemo 测试"""

    def test_demo_instance(self) -> None:
        """测试演示实例化"""
        demo = CodeQADemo()
        assert demo.plugin is not None


class TestMatchRule:
    """MatchRule 测试"""

    def test_default_priority(self) -> None:
        """测试默认优先级"""
        rule = MatchRule(keyword="test", answer="answer")
        assert rule.priority == 0

    def test_custom_priority(self) -> None:
        """测试自定义优先级"""
        rule = MatchRule(keyword="test", answer="answer", priority=5)
        assert rule.priority == 5


class TestKeywordMatchPlugin:
    """KeywordMatchPlugin 测试"""

    def test_add_rule(self) -> None:
        """测试添加规则"""
        plugin = KeywordMatchPlugin()
        plugin.add_rule(MatchRule("Python", "编程语言"))
        assert plugin.count_rules() == 1

    def test_add_rules(self) -> None:
        """测试批量添加规则"""
        plugin = KeywordMatchPlugin()
        plugin.add_rules(
            [
                MatchRule("a", "1"),
                MatchRule("b", "2"),
            ]
        )
        assert plugin.count_rules() == 2

    def test_match_found(self) -> None:
        """测试匹配成功"""
        plugin = KeywordMatchPlugin()
        plugin.add_rule(MatchRule("Python", "编程语言", priority=5))
        result = plugin.match("什么是 Python")
        assert result["matched"] is True
        assert result["keyword"] == "Python"

    def test_match_not_found(self) -> None:
        """测试匹配失败"""
        plugin = KeywordMatchPlugin()
        result = plugin.match("Java 是什么")
        assert result["matched"] is False

    def test_priority_sorting(self) -> None:
        """测试优先级排序"""
        plugin = KeywordMatchPlugin()
        plugin.add_rules(
            [
                MatchRule("a", "低优先级", priority=1),
                MatchRule("b", "高优先级", priority=5),
            ]
        )
        result = plugin.match("a 和 b")
        assert result["keyword"] == "b"  # 高优先级

    def test_match_all(self) -> None:
        """测试返回所有匹配"""
        plugin = KeywordMatchPlugin()
        plugin.add_rules(
            [
                MatchRule("Python", "Python", priority=1),
                MatchRule("编程", "编程", priority=2),
            ]
        )
        results = plugin.match_all("Python 编程")
        assert len(results) == 2

    def test_clear_rules(self) -> None:
        """测试清空规则"""
        plugin = KeywordMatchPlugin()
        plugin.add_rule(MatchRule("a", "1"))
        plugin.clear_rules()
        assert plugin.count_rules() == 0


class TestKeywordMatchDemo:
    """KeywordMatchDemo 测试"""

    def test_demo_instance(self) -> None:
        """测试演示实例化"""
        demo = KeywordMatchDemo()
        assert demo.plugin is not None
        assert demo.plugin.count_rules() > 0


class TestPluginRegistry:
    """PluginRegistry 测试"""

    def test_register(self) -> None:
        """测试注册插件"""
        registry = PluginRegistry()
        registry.register("test", lambda q: "result")
        assert "test" in registry.list_plugins()

    def test_get_plugin(self) -> None:
        """测试获取插件"""
        registry = PluginRegistry()
        registry.register("test", lambda q: "result")
        handler = registry.get_plugin("test")
        assert handler is not None
        assert handler("query") == "result"

    def test_get_nonexistent_plugin(self) -> None:
        """测试获取不存在的插件"""
        registry = PluginRegistry()
        handler = registry.get_plugin("nonexistent")
        assert handler is None

    def test_execute(self) -> None:
        """测试执行插件"""
        registry = PluginRegistry()
        registry.register("test", lambda q: f"处理: {q}")
        result = registry.execute("test", "问题")
        assert result == "处理: 问题"

    def test_execute_nonexistent(self) -> None:
        """测试执行不存在的插件"""
        registry = PluginRegistry()
        result = registry.execute("nonexistent", "问题")
        assert "不存在" in result

    def test_get_tools(self) -> None:
        """测试获取 LangChain 工具"""
        registry = PluginRegistry()
        registry.register("test", lambda q: "result")
        tools = registry.get_tools()
        assert len(tools) == 1


class TestToolNode:
    """ToolNode 测试"""

    def test_call_with_tool_name(self) -> None:
        """测试指定工具名调用"""
        registry = PluginRegistry()
        registry.register("test", lambda q: "result")

        node = ToolNode(registry)
        state = {
            "query": "问题",
            "tool_name": "test",
            "result": "",
            "messages": [],
        }
        result = node(state)
        assert result["result"] == "result"
        assert result["tool_name"] == "test"

    def test_call_auto_select(self) -> None:
        """测试自动选择工具"""
        registry = PluginRegistry()
        registry.register("python", lambda q: "python result")

        node = ToolNode(registry)
        state = {
            "query": "Python 问题",
            "tool_name": "",
            "result": "",
            "messages": [],
        }
        result = node(state)
        assert result["tool_name"] == "python"


class TestPluginIntegrationDemo:
    """PluginIntegrationDemo 测试"""

    def test_demo_instance(self) -> None:
        """测试演示实例化"""
        demo = PluginIntegrationDemo()
        assert demo.registry is not None
        assert len(demo.registry.list_plugins()) == 2
