"""插件市场适配器"""

from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter
from tenant.services.marketplace.adapters.modelscope_adapter import ModelScopeAdapter
from tenant.services.marketplace.adapters.agentskills_adapter import AgentSkillsAdapter
from tenant.services.marketplace.adapters.modelscope_skill_adapter import (
    ModelScopeSkillAdapter,
)
from tenant.services.marketplace.adapters.local_skill_adapter import LocalSkillAdapter
from tenant.services.marketplace.adapters.local_plugin_adapter import LocalPluginAdapter

__all__ = [
    "DifyAdapter",
    "ModelScopeAdapter",
    "AgentSkillsAdapter",
    "ModelScopeSkillAdapter",
    "LocalSkillAdapter",
    "LocalPluginAdapter",
]
