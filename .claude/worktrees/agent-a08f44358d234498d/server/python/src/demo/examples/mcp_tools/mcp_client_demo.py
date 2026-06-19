"""
MCP 客户端配置示例

演示如何配置 MCP (Model Context Protocol) 客户端，
连接到 MCP 服务器并发现可用工具。

Day 3 讲义：AI 智能体应用实战 - MCP 工具集成

注意：本示例提供模拟实现，实际使用需要配置真实的 MCP 服务器。
"""

from typing import Any

from pydantic import BaseModel


# ==================== 配置模型 ====================


class MCPClientConfig(BaseModel):
    """
    MCP 客户端配置

    定义连接 MCP 服务器所需的参数。
    """

    # 服务器名称
    server_name: str

    # 服务器命令（启动 MCP 服务器的命令）
    command: str

    # 命令参数
    args: list[str] = []

    # 环境变量
    env: dict[str, str] = {}

    # 连接超时（秒）
    timeout: int = 30


# ==================== 模拟 MCP 工具 ====================


class MockMCPTool:
    """模拟 MCP 工具"""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
    ) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def invoke(self, arguments: dict[str, Any]) -> str:
        """调用工具"""
        # 模拟工具执行
        return f"[{self.name}] 执行成功，参数：{arguments}"


# ==================== MCP 客户端演示类 ====================


class MCPClientDemo:
    """
    MCP 客户端演示

    展示如何配置和连接 MCP 服务器。
    使用模拟实现，无需真实的 MCP 服务器。
    """

    def __init__(self, config: MCPClientConfig) -> None:
        """
        初始化 MCP 客户端

        Args:
            config: 客户端配置
        """
        self.config = config
        self._connected = False
        self._tools: dict[str, MockMCPTool] = {}

        # 初始化模拟工具
        self._init_mock_tools()

    def _init_mock_tools(self) -> None:
        """初始化模拟工具"""
        # 模拟文件系统工具
        self._tools["read_file"] = MockMCPTool(
            name="read_file",
            description="读取文件内容",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径",
                    }
                },
                "required": ["path"],
            },
        )

        # 模拟搜索工具
        self._tools["web_search"] = MockMCPTool(
            name="web_search",
            description="搜索网络内容",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        )

        # 模拟数据库查询工具
        self._tools["query_database"] = MockMCPTool(
            name="query_database",
            description="执行数据库查询",
            input_schema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL 查询语句",
                    },
                },
                "required": ["sql"],
            },
        )

    async def connect(self) -> bool:
        """
        连接到 MCP 服务器

        Returns:
            是否连接成功
        """
        # 模拟连接过程
        print(f"正在连接到 MCP 服务器 '{self.config.server_name}'...")
        print(f"  命令: {self.config.command} {' '.join(self.config.args)}")

        # 模拟连接延迟
        import asyncio

        await asyncio.sleep(0.1)

        self._connected = True
        print(f"[OK] 已连接到 '{self.config.server_name}'")

        return True

    async def disconnect(self) -> None:
        """断开连接"""
        self._connected = False
        print(f"已断开与 '{self.config.server_name}' 的连接")

    def list_tools(self) -> list[dict[str, Any]]:
        """
        列出所有可用工具

        Returns:
            工具列表
        """
        if not self._connected:
            raise RuntimeError("未连接到 MCP 服务器")

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    def get_tool(self, name: str) -> MockMCPTool | None:
        """
        获取指定工具

        Args:
            name: 工具名称

        Returns:
            工具对象或 None
        """
        return self._tools.get(name)

    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """
        调用工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        if not self._connected:
            raise RuntimeError("未连接到 MCP 服务器")

        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"未找到工具: {tool_name}")

        return tool.invoke(arguments)


# ==================== 多服务器配置 ====================


class MultiMCPClient:
    """
    多 MCP 服务器客户端

    支持同时连接多个 MCP 服务器。
    """

    def __init__(self) -> None:
        """初始化多服务器客户端"""
        self._clients: dict[str, MCPClientDemo] = {}

    async def add_server(self, config: MCPClientConfig) -> bool:
        """
        添加并连接到服务器

        Args:
            config: 服务器配置

        Returns:
            是否连接成功
        """
        client = MCPClientDemo(config)
        success = await client.connect()

        if success:
            self._clients[config.server_name] = client

        return success

    async def remove_server(self, server_name: str) -> None:
        """移除服务器"""
        client = self._clients.pop(server_name, None)
        if client:
            await client.disconnect()

    def list_all_tools(self) -> dict[str, list[dict[str, Any]]]:
        """
        列出所有服务器的工具

        Returns:
            按服务器分组的工具列表
        """
        result = {}

        for server_name, client in self._clients.items():
            result[server_name] = client.list_tools()

        return result

    async def invoke_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> str:
        """调用指定服务器的工具"""
        client = self._clients.get(server_name)
        if not client:
            raise ValueError(f"未找到服务器: {server_name}")

        return await client.invoke_tool(tool_name, arguments)


# ==================== 演示函数 ====================


async def demo_mcp_client() -> None:
    """演示 MCP 客户端"""
    print("=== MCP 客户端演示 ===\n")

    # 创建配置
    config = MCPClientConfig(
        server_name="demo-server",
        command="python",
        args=["-m", "mcp_server"],
        env={"DEBUG": "1"},
    )

    # 创建客户端
    client = MCPClientDemo(config)

    # 连接
    await client.connect()
    print()

    # 列出工具
    print("可用工具：")
    tools = client.list_tools()
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
        print(f"    参数: {list(tool['input_schema']['properties'].keys())}")
    print()

    # 调用工具
    print("调用工具：")

    result1 = await client.invoke_tool("read_file", {"path": "/tmp/test.txt"})
    print(f"  read_file: {result1}")

    result2 = await client.invoke_tool("web_search", {"query": "LangChain", "limit": 3})
    print(f"  web_search: {result2}")

    # 断开连接
    await client.disconnect()


async def demo_multi_server() -> None:
    """演示多服务器配置"""
    print("\n=== 多 MCP 服务器演示 ===\n")

    client = MultiMCPClient()

    # 添加多个服务器
    configs = [
        MCPClientConfig(
            server_name="filesystem",
            command="mcp-filesystem",
            args=["--root", "/data"],
        ),
        MCPClientConfig(
            server_name="database",
            command="mcp-postgres",
            args=["--connection", "postgresql://localhost/db"],
        ),
    ]

    for config in configs:
        await client.add_server(config)
        print()

    # 列出所有工具
    print("所有服务器工具：")
    all_tools = client.list_all_tools()
    for server_name, tools in all_tools.items():
        print(f"\n{server_name}:")
        for tool in tools:
            print(f"  - {tool['name']}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_mcp_client())
    asyncio.run(demo_multi_server())
