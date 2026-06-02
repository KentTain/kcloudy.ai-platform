"""
AI 模块控制器层

包含 admin、console、inner 三层控制器。
"""

from ai.controllers.admin import plugin_router as admin_plugin_router
from ai.controllers.console import plugin_router as console_plugin_router
from ai.controllers.inner import plugin_router as inner_plugin_router

__all__ = [
    "admin_plugin_router",
    "console_plugin_router",
    "inner_plugin_router",
]
