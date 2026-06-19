"""
AI 智能体应用实战示例模块

本模块包含 LangChain 和 LangGraph 的演示代码，涵盖：
- 提示词工程（Prompt Engineering）
- 自定义工具开发（Custom Tools）
- LangGraph 工作流编排
- MCP 工具集成

用于 Day 3 讲义：AI 智能体应用实战

注意：此模块需要安装 langchain 依赖组：
    uv sync --group langchain
"""

try:
    from demo.examples import (
        custom_tools,
        langgraph_workflows,
        mcp_tools,
        prompt_engineering,
    )

    __all__ = [
        "prompt_engineering",
        "custom_tools",
        "langgraph_workflows",
        "mcp_tools",
    ]
except ImportError:
    # langchain 可选依赖未安装时，优雅降级
    __all__ = []
