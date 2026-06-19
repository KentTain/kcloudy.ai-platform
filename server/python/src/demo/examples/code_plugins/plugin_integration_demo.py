"""
插件与 LangGraph 集成示例

演示如何将代码插件集成到 LangGraph 工作流：
- 插件注册表
- 工具节点
- 工作流编排

示例使用：
    registry = PluginRegistry()
    registry.register(code_plugin)
    node = ToolNode(registry)
"""

from collections.abc import Callable
from typing import Any

from langchain_core.tools import StructuredTool
from typing_extensions import TypedDict


class ToolState(TypedDict):
    """工具状态"""

    query: str
    tool_name: str
    result: str
    messages: list[dict[str, str]]


class PluginRegistry:
    """插件注册表

    管理所有注册的代码插件。
    """

    def __init__(self) -> None:
        """初始化注册表"""
        self._plugins: dict[str, Callable[[str], str]] = {}
        self._tools: list[Any] = []

    def register(
        self,
        name: str,
        handler: Callable[[str], str],
        description: str = "",
    ) -> None:
        """注册插件

        Args:
            name: 插件名称
            handler: 处理函数
            description: 插件描述
        """
        self._plugins[name] = handler

        # 创建 LangChain 工具
        def plugin_func(query: str) -> str:
            return handler(query)

        plugin_func.__name__ = name
        plugin_func.__doc__ = description or f"{name} 插件"

        langchain_tool = StructuredTool.from_function(
            func=plugin_func,
            name=name,
            description=description or f"{name} 插件",
        )

        self._tools.append(langchain_tool)

    def get_plugin(self, name: str) -> Callable[[str], str] | None:
        """获取插件

        Args:
            name: 插件名称

        Returns:
            插件处理函数
        """
        return self._plugins.get(name)

    def get_tools(self) -> list[Any]:
        """获取所有 LangChain 工具"""
        return self._tools.copy()

    def list_plugins(self) -> list[str]:
        """列出所有插件名称"""
        return list(self._plugins.keys())

    def execute(self, name: str, query: str) -> str:
        """执行插件

        Args:
            name: 插件名称
            query: 查询内容

        Returns:
            执行结果
        """
        handler = self.get_plugin(name)
        if handler is None:
            return f"插件 '{name}' 不存在"
        return handler(query)


class ToolNode:
    """工具节点

    用于 LangGraph 工作流的工具调用节点。
    """

    def __init__(self, registry: PluginRegistry) -> None:
        """初始化工具节点

        Args:
            registry: 插件注册表
        """
        self.registry = registry

    def __call__(self, state: ToolState) -> dict[str, Any]:
        """执行工具调用

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        query = state["query"]
        tool_name = state.get("tool_name", "")

        # 如果没有指定工具，尝试自动选择
        if not tool_name:
            tool_name = self._auto_select_tool(query)

        result = self.registry.execute(tool_name, query)

        return {
            "tool_name": tool_name,
            "result": result,
            "messages": [
                *state.get("messages", []),
                {"role": "tool", "content": result, "name": tool_name},
            ],
        }

    def _auto_select_tool(self, query: str) -> str:
        """自动选择工具

        Args:
            query: 查询内容

        Returns:
            工具名称
        """
        plugins = self.registry.list_plugins()
        if not plugins:
            return ""

        # 简单的关键词匹配
        query_lower = query.lower()
        for name in plugins:
            if name.lower() in query_lower:
                return name

        # 默认返回第一个插件
        return plugins[0] if plugins else ""


class PluginIntegrationDemo:
    """插件集成演示类"""

    def __init__(self) -> None:
        """初始化演示"""
        self.registry = PluginRegistry()

        # 注册示例插件
        self.registry.register(
            name="python_qa",
            handler=self._python_qa_handler,
            description="Python 代码问答",
        )

        self.registry.register(
            name="code_generator",
            handler=self._code_generator_handler,
            description="代码生成器",
        )

    def _python_qa_handler(self, query: str) -> str:
        """Python QA 处理器"""
        if "函数" in query:
            return "def example(): pass"
        if "类" in query:
            return "class Example: pass"
        return "未找到相关 Python 代码"

    def _code_generator_handler(self, query: str) -> str:
        """代码生成处理器"""
        return f"# 生成代码: {query}\n# 实现中..."

    def run_demo(self) -> None:
        """运行演示"""
        print("=" * 50)
        print("插件与 LangGraph 集成示例")
        print("=" * 50)

        # 显示注册的插件
        print(f"\n已注册插件: {self.registry.list_plugins()}")

        # 获取 LangChain 工具
        tools = self.registry.get_tools()
        print(f"LangChain 工具数: {len(tools)}")
        for t in tools:
            print(f"  - {t.name}: {t.description[:30]}...")

        # 执行插件
        print("\n执行插件:")
        result1 = self.registry.execute("python_qa", "Python 函数示例")
        print(f"  python_qa: {result1}")

        result2 = self.registry.execute("code_generator", "排序算法")
        print(f"  code_generator: {result2}")

        # 工具节点演示
        print("\n工具节点演示:")
        node = ToolNode(self.registry)
        state: ToolState = {
            "query": "如何定义 Python 类？",
            "tool_name": "python_qa",
            "result": "",
            "messages": [],
        }
        result = node(state)
        print(f"  工具: {result['tool_name']}")
        print(f"  结果: {result['result']}")


def demo() -> None:
    """演示插件集成功能"""
    demo_instance = PluginIntegrationDemo()
    demo_instance.run_demo()


if __name__ == "__main__":
    demo()
