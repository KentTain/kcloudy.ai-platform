"""
AI 智能体应用实战示例模块

本模块包含 LangChain 和 LangGraph 的演示代码，涵盖：
- 提示词工程（Prompt Engineering）
- 自定义工具开发（Custom Tools）
- LangGraph 工作流编排
- MCP 工具集成

用于 Day 3 讲义：AI 智能体应用实战
"""

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
