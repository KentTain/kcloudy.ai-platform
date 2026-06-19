"""
自定义工具示例模块

演示 LangChain 工具开发：
- @tool 装饰器：快速创建简单工具
- StructuredTool：复杂结构化工具
- 工具链编排：多工具协同工作
"""

try:
    from demo.examples.custom_tools.basic_tool_demo import (
        CalculatorTool,
        create_weather_tool,
        demo_basic_tools,
    )
    from demo.examples.custom_tools.structured_tool_demo import (
        DatabaseQueryTool,
        SearchTool,
    )
    from demo.examples.custom_tools.tool_chain_demo import (
        SimpleToolChain,
        demo_tool_chain,
    )

    __all__ = [
        "create_weather_tool",
        "CalculatorTool",
        "demo_basic_tools",
        "SearchTool",
        "DatabaseQueryTool",
        "SimpleToolChain",
        "demo_tool_chain",
    ]
except ImportError:
    # langchain 可选依赖未安装时，优雅降级
    __all__ = []
