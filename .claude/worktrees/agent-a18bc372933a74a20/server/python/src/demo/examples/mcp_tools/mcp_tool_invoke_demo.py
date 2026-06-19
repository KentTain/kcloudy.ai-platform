"""
MCP 工具调用示例

演示如何通过 LangChain 调用 MCP 工具。
将 MCP 工具包装为 LangChain 工具格式。

Day 3 讲义：AI 智能体应用实战 - MCP 工具集成
"""

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


# ==================== MCP 工具包装器 ====================


class MCPToolWrapper:
    """
    MCP 工具包装器

    将 MCP 工具包装为 LangChain 工具格式，
    使其可以在 LangChain 智能体中使用。
    """

    def __init__(
        self,
        tool_name: str,
        tool_description: str,
        input_schema: dict[str, Any],
        executor: Any = None,
    ) -> None:
        """
        初始化工具包装器

        Args:
            tool_name: 工具名称
            tool_description: 工具描述
            input_schema: 输入参数 schema
            executor: 工具执行器（模拟）
        """
        self.tool_name = tool_name
        self.tool_description = tool_description
        self.input_schema = input_schema
        self.executor = executor or self._default_executor

        # 动态创建 Pydantic 模型
        self.args_schema = self._create_args_model()

    def _default_executor(self, **kwargs: Any) -> str:
        """默认执行器（模拟）"""
        return f"[{self.tool_name}] 执行成功，参数：{kwargs}"

    def _create_args_model(self) -> type[BaseModel]:
        """
        根据输入 schema 创建 Pydantic 模型

        Returns:
            Pydantic 模型类
        """
        # 简化的模型创建
        fields = {}
        annotations = {}

        properties = self.input_schema.get("properties", {})
        required = set(self.input_schema.get("required", []))

        for field_name, field_spec in properties.items():
            field_type = str  # 默认类型
            field_desc = field_spec.get("description", "")

            annotations[field_name] = field_type

            if field_name in required:
                fields[field_name] = Field(description=field_desc)
            else:
                default_val = field_spec.get("default", None)
                fields[field_name] = Field(default=default_val, description=field_desc)

        # 动态创建模型
        model_name = f"{self.tool_name.title().replace('_', '')}Input"
        fields["__annotations__"] = annotations
        return type(model_name, (BaseModel,), fields)

    def to_langchain_tool(self) -> StructuredTool:
        """
        转换为 LangChain StructuredTool

        Returns:
            StructuredTool 实例
        """
        return StructuredTool(
            name=self.tool_name,
            description=self.tool_description,
            func=self.executor,
            args_schema=self.args_schema,
        )


# ==================== MCP 工具调用器 ====================


class MCPToolInvoker:
    """
    MCP 工具调用器

    管理多个 MCP 工具的调用。
    """

    def __init__(self) -> None:
        """初始化工具调用器"""
        self._tools: dict[str, MCPToolWrapper] = {}
        self._langchain_tools: dict[str, StructuredTool] = {}

        # 初始化默认工具
        self._init_default_tools()

    def _init_default_tools(self) -> None:
        """初始化默认的 MCP 工具"""

        # 文件读取工具
        self.register_tool(
            tool_name="mcp_read_file",
            tool_description="通过 MCP 读取文件内容",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "文件编码",
                        "default": "utf-8",
                    },
                },
                "required": ["path"],
            },
            executor=lambda path,
            encoding="utf-8": f"[MCP] 读取文件: {path} (编码: {encoding})",
        )

        # 网络搜索工具
        self.register_tool(
            tool_name="mcp_web_search",
            tool_description="通过 MCP 搜索网络",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词",
                    },
                    "engine": {
                        "type": "string",
                        "description": "搜索引擎",
                        "default": "google",
                    },
                },
                "required": ["query"],
            },
            executor=lambda query,
            engine="google": f"[MCP] 搜索 '{query}' (引擎: {engine})",
        )

        # 天气查询工具
        self.register_tool(
            tool_name="mcp_weather",
            tool_description="通过 MCP 查询天气",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称",
                    },
                    "units": {
                        "type": "string",
                        "description": "温度单位",
                        "default": "celsius",
                    },
                },
                "required": ["city"],
            },
            executor=lambda city,
            units="celsius": f"[MCP] {city} 天气: 晴朗, 25°{'C' if units == 'celsius' else 'F'}",
        )

        # 数据库查询工具
        self.register_tool(
            tool_name="mcp_db_query",
            tool_description="通过 MCP 执行数据库查询",
            input_schema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "数据库名称",
                    },
                    "query": {
                        "type": "string",
                        "description": "查询语句",
                    },
                },
                "required": ["database", "query"],
            },
            executor=lambda database, query: f"[MCP] 数据库 '{database}' 执行: {query}",
        )

    def register_tool(
        self,
        tool_name: str,
        tool_description: str,
        input_schema: dict[str, Any],
        executor: Any = None,
    ) -> None:
        """
        注册新工具

        Args:
            tool_name: 工具名称
            tool_description: 工具描述
            input_schema: 输入参数 schema
            executor: 工具执行器
        """
        wrapper = MCPToolWrapper(
            tool_name=tool_name,
            tool_description=tool_description,
            input_schema=input_schema,
            executor=executor,
        )

        self._tools[tool_name] = wrapper
        self._langchain_tools[tool_name] = wrapper.to_langchain_tool()

    def get_tool(self, name: str) -> StructuredTool | None:
        """
        获取 LangChain 工具

        Args:
            name: 工具名称

        Returns:
            StructuredTool 实例或 None
        """
        return self._langchain_tools.get(name)

    def list_tools(self) -> list[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def get_langchain_tools(self) -> list[StructuredTool]:
        """
        获取所有 LangChain 工具

        Returns:
            StructuredTool 列表
        """
        return list(self._langchain_tools.values())

    def invoke(self, tool_name: str, **kwargs: Any) -> str:
        """
        调用工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        tool = self._langchain_tools.get(tool_name)
        if not tool:
            raise ValueError(f"未找到工具: {tool_name}")

        return tool.invoke(kwargs)


# ==================== 演示函数 ====================


def demo_tool_invoke() -> None:
    """演示工具调用"""
    print("=== MCP 工具调用演示 ===\n")

    # 创建工具调用器
    invoker = MCPToolInvoker()

    # 列出可用工具
    print("可用工具：")
    for name in invoker.list_tools():
        tool = invoker.get_tool(name)
        if tool:
            print(f"  - {name}: {tool.description}")
    print()

    # 调用工具
    print("调用工具示例：")

    # 读取文件
    result1 = invoker.invoke("mcp_read_file", path="/data/test.txt")
    print(f"\n1. {result1}")

    # 搜索
    result2 = invoker.invoke("mcp_web_search", query="LangChain 教程")
    print(f"2. {result2}")

    # 天气
    result3 = invoker.invoke("mcp_weather", city="北京")
    print(f"3. {result3}")

    # 数据库查询
    result4 = invoker.invoke(
        "mcp_db_query", database="users", query="SELECT * FROM users LIMIT 10"
    )
    print(f"4. {result4}")


def demo_tool_as_langchain() -> None:
    """演示作为 LangChain 工具使用"""
    print("\n=== 作为 LangChain 工具使用 ===\n")

    invoker = MCPToolInvoker()
    tools = invoker.get_langchain_tools()

    print(f"已注册 {len(tools)} 个 LangChain 工具：\n")

    for tool in tools:
        print(f"工具名: {tool.name}")
        print(f"描述: {tool.description}")
        schema_name = (
            getattr(tool.args_schema, "__name__", "dict")
            if tool.args_schema
            else "None"
        )
        print(f"参数模型: {schema_name}")
        print()


def demo_custom_tool() -> None:
    """演示注册自定义工具"""
    print("\n=== 注册自定义 MCP 工具 ===\n")

    invoker = MCPToolInvoker()

    # 注册自定义翻译工具
    invoker.register_tool(
        tool_name="mcp_translate",
        tool_description="通过 MCP 翻译文本",
        input_schema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要翻译的文本",
                },
                "source_lang": {
                    "type": "string",
                    "description": "源语言",
                    "default": "auto",
                },
                "target_lang": {
                    "type": "string",
                    "description": "目标语言",
                },
            },
            "required": ["text", "target_lang"],
        },
        executor=lambda text,
        target_lang,
        source_lang="auto": f"[MCP] 翻译 '{text}' ({source_lang} -> {target_lang})",
    )

    # 调用自定义工具
    result = invoker.invoke(
        "mcp_translate",
        text="Hello World",
        target_lang="zh",
    )
    print(result)


if __name__ == "__main__":
    demo_tool_invoke()
    demo_tool_as_langchain()
    demo_custom_tool()
