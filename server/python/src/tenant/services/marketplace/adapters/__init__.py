"""插件市场适配器"""

from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter
from tenant.services.marketplace.adapters.git_skills_adapter import GitSkillsAdapter
from tenant.services.marketplace.adapters.modelscope_skill_adapter import (
    ModelScopeSkillAdapter,
)
from tenant.services.marketplace.adapters.modelscope_mcp_adapter import (
    ModelScopeMcpAdapter,
)
from tenant.services.marketplace.adapters.local_skill_adapter import LocalSkillAdapter
from tenant.services.marketplace.adapters.local_plugin_adapter import LocalPluginAdapter

__all__ = [
    "DifyAdapter",
    "GitSkillsAdapter",
    "ModelScopeSkillAdapter",
    "ModelScopeMcpAdapter",
    "LocalSkillAdapter",
    "LocalPluginAdapter",
]
