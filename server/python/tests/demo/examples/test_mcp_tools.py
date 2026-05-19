"""
MCP 工具示例单元测试

测试 mcp_tools 模块的所有示例代码。
"""

import pytest

from demo.examples.mcp_tools.mcp_client_demo import (
    MCPClientConfig,
    MCPClientDemo,
    MultiMCPClient,
)
from demo.examples.mcp_tools.mcp_langgraph_demo import (
    AgentState,
    MCPAgentGraph,
    ReActAgentGraph,
)
from demo.examples.mcp_tools.mcp_tool_invoke_demo import (
    MCPToolInvoker,
    MCPToolWrapper,
)


class TestMCPClientConfig:
    """测试 MCP 客户端配置"""

    def test_config_creation(self) -> None:
        """测试创建配置"""
        config = MCPClientConfig(
            server_name="test-server",
            command="python",
            args=["-m", "mcp_server"],
        )

        assert config.server_name == "test-server"
        assert config.command == "python"
        assert config.args == ["-m", "mcp_server"]
        assert config.timeout == 30

    def test_config_with_env(self) -> None:
        """测试带环境变量的配置"""
        config = MCPClientConfig(
            server_name="test-server",
            command="node",
            args=["server.js"],
            env={"API_KEY": "secret"},
            timeout=60,
        )

        assert config.env == {"API_KEY": "secret"}
        assert config.timeout == 60


class TestMCPClientDemo:
    """测试 MCP 客户端演示"""

    @pytest.mark.asyncio
    async def test_connect(self) -> None:
        """测试连接"""
        config = MCPClientConfig(
            server_name="demo",
            command="test",
        )
        client = MCPClientDemo(config)

        success = await client.connect()
        assert success is True

    @pytest.mark.asyncio
    async def test_list_tools(self) -> None:
        """测试列出工具"""
        config = MCPClientConfig(
            server_name="demo",
            command="test",
        )
        client = MCPClientDemo(config)
        await client.connect()

        tools = client.list_tools()
        assert len(tools) > 0
        assert any(t["name"] == "read_file" for t in tools)

    @pytest.mark.asyncio
    async def test_invoke_tool(self) -> None:
        """测试调用工具"""
        config = MCPClientConfig(
            server_name="demo",
            command="test",
        )
        client = MCPClientDemo(config)
        await client.connect()

        result = await client.invoke_tool("read_file", {"path": "/test.txt"})
        assert "read_file" in result

    @pytest.mark.asyncio
    async def test_invoke_nonexistent_tool(self) -> None:
        """测试调用不存在的工具"""
        config = MCPClientConfig(
            server_name="demo",
            command="test",
        )
        client = MCPClientDemo(config)
        await client.connect()

        with pytest.raises(ValueError, match="未找到工具"):
            await client.invoke_tool("nonexistent", {})

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        """测试断开连接"""
        config = MCPClientConfig(
            server_name="demo",
            command="test",
        )
        client = MCPClientDemo(config)
        await client.connect()

        await client.disconnect()


class TestMultiMCPClient:
    """测试多服务器客户端"""

    @pytest.mark.asyncio
    async def test_add_server(self) -> None:
        """测试添加服务器"""
        client = MultiMCPClient()

        config = MCPClientConfig(
            server_name="test",
            command="test",
        )
        success = await client.add_server(config)

        assert success is True

    @pytest.mark.asyncio
    async def test_list_all_tools(self) -> None:
        """测试列出所有工具"""
        client = MultiMCPClient()

        config = MCPClientConfig(
            server_name="test",
            command="test",
        )
        await client.add_server(config)

        all_tools = client.list_all_tools()
        assert "test" in all_tools


class TestMCPToolWrapper:
    """测试 MCP 工具包装器"""

    def test_wrapper_creation(self) -> None:
        """测试创建包装器"""
        wrapper = MCPToolWrapper(
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "查询"},
                },
                "required": ["query"],
            },
        )

        assert wrapper.tool_name == "test_tool"
        assert wrapper.tool_description == "测试工具"

    def test_to_langchain_tool(self) -> None:
        """测试转换为 LangChain 工具"""
        wrapper = MCPToolWrapper(
            tool_name="test_tool",
            tool_description="测试工具",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "查询"},
                },
                "required": ["query"],
            },
        )

        tool = wrapper.to_langchain_tool()

        assert tool.name == "test_tool"
        assert tool.description == "测试工具"


class TestMCPToolInvoker:
    """测试 MCP 工具调用器"""

    def test_list_tools(self) -> None:
        """测试列出工具"""
        invoker = MCPToolInvoker()

        tools = invoker.list_tools()
        assert "mcp_read_file" in tools
        assert "mcp_web_search" in tools

    def test_invoke_tool(self) -> None:
        """测试调用工具"""
        invoker = MCPToolInvoker()

        result = invoker.invoke("mcp_weather", city="北京")
        assert "北京" in result
        assert "天气" in result

    def test_invoke_nonexistent_tool(self) -> None:
        """测试调用不存在的工具"""
        invoker = MCPToolInvoker()

        with pytest.raises(ValueError, match="未找到工具"):
            invoker.invoke("nonexistent_tool")

    def test_get_langchain_tools(self) -> None:
        """测试获取 LangChain 工具列表"""
        invoker = MCPToolInvoker()

        tools = invoker.get_langchain_tools()
        assert len(tools) > 0

        # 验证工具属性
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")

    def test_register_custom_tool(self) -> None:
        """测试注册自定义工具"""
        invoker = MCPToolInvoker()

        invoker.register_tool(
            tool_name="custom_tool",
            tool_description="自定义工具",
            input_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "输入"},
                },
                "required": ["input"],
            },
            executor=lambda input: f"处理: {input}",
        )

        assert "custom_tool" in invoker.list_tools()

        result = invoker.invoke("custom_tool", input="test")
        assert "test" in result


class TestMCPAgentGraph:
    """测试 MCP 智能体图"""

    def test_agent_weather_request(self) -> None:
        """测试天气请求"""
        agent = MCPAgentGraph()

        result = agent.run("今天天气怎么样？")

        assert result["action"] == "call_tool"
        assert result["tool_name"] == "mcp_weather"
        assert "天气" in result["response"]

    def test_agent_search_request(self) -> None:
        """测试搜索请求"""
        agent = MCPAgentGraph()

        result = agent.run("帮我搜索一下")

        assert result["action"] == "call_tool"
        assert result["tool_name"] == "mcp_search"

    def test_agent_general_request(self) -> None:
        """测试一般请求"""
        agent = MCPAgentGraph()

        result = agent.run("随便聊聊")

        assert result["action"] == "respond_directly"
        assert result["tool_name"] == ""

    def test_agent_state_persistence(self) -> None:
        """测试状态持久化"""
        agent = MCPAgentGraph()

        result = agent.run("测试请求")

        assert len(result["messages"]) > 0
        assert result["iterations"] == 1


class TestReActAgentGraph:
    """测试 ReAct 智能体图"""

    def test_react_agent_execution(self) -> None:
        """测试 ReAct 智能体执行"""
        agent = ReActAgentGraph(max_iterations=2)

        result = agent.run("测试请求")

        assert result["response"]
        assert result["iterations"] > 0

    def test_react_agent_iterations(self) -> None:
        """测试 ReAct 智能体迭代次数"""
        agent = ReActAgentGraph(max_iterations=1)

        result = agent.run("测试请求")

        assert result["iterations"] <= 2  # think + act


class TestAgentState:
    """测试智能体状态模型"""

    def test_state_creation(self) -> None:
        """测试创建状态"""
        state = AgentState(user_request="测试")

        assert state.user_request == "测试"
        assert state.action == ""
        assert state.tool_name == ""
        assert state.messages == []

    def test_state_serialization(self) -> None:
        """测试状态序列化"""
        state = AgentState(
            user_request="测试",
            action="call_tool",
            tool_name="test_tool",
        )
        state_dict = state.model_dump()

        assert "user_request" in state_dict
        assert "action" in state_dict
        assert "tool_name" in state_dict
