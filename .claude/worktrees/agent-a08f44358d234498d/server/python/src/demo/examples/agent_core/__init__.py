"""
智能体核心逻辑示例模块

本模块演示智能体开发的四大支柱：
- 人设（Persona）：角色、语气、系统提示词
- 知识库（Knowledge）：检索增强生成
- 插件（Plugins）：HTTP 工具和代码工具
- 工作流（Workflow）：LangGraph 状态编排

示例使用：
    from demo.examples.agent_core import PersonaConfig, AgentWorkflow
"""

from demo.examples.agent_core.persona_demo import (
    AgentPersona,
    PersonaConfig,
    PersonaDemo,
)
from demo.examples.agent_core.knowledge_base_demo import (
    AgentKnowledgeBase,
    KnowledgeBaseDemo,
    MockRetriever,
)
from demo.examples.agent_core.workflow_demo import (
    AgentState,
    AgentWorkflow,
    WorkflowDemo,
)
from demo.examples.agent_core.agent_demo import (
    AgentDemo,
    SimpleAgent,
)

__all__ = [
    "AgentPersona",
    "PersonaConfig",
    "PersonaDemo",
    "AgentKnowledgeBase",
    "KnowledgeBaseDemo",
    "MockRetriever",
    "AgentState",
    "AgentWorkflow",
    "WorkflowDemo",
    "SimpleAgent",
    "AgentDemo",
]
