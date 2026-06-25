"""
AI 模块控制台控制器
"""

from ai.controllers.console.installations import router as installations_router
from ai.controllers.console.plugin import router as plugin_router
from ai.controllers.console.runtime_states import router as runtime_states_router

__all__ = ["plugin_router", "installations_router", "runtime_states_router"]
