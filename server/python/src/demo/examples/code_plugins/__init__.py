"""
代码插件示例模块

本模块演示代码插件开发：
- 代码问答插件
- 关键词匹配插件
- LangGraph 集成

示例使用：
    from demo.examples.code_plugins import CodeQAPlugin, KeywordMatchPlugin
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

__all__ = [
    "CodeQAPlugin",
    "CodeQADemo",
    "PythonCodeQA",
    "KeywordMatchDemo",
    "KeywordMatchPlugin",
    "MatchRule",
    "PluginIntegrationDemo",
    "PluginRegistry",
    "ToolNode",
]
