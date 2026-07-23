"""
插件模型子包

包含插件相关模型：PluginCredential、PluginInstallTask、PluginConfig 等
"""

from .plugin import (
    CredentialScope,
    InstallType,
    PluginCredential,
    PluginInstallTask,
    PluginStatus,
    PluginType,
    RuntimeType,
    SourceType,
    TaskStatus,
)
from .plugin_config import PluginConfig
from .plugin_default_model import PluginDefaultModel
from .plugin_runtime_state import PluginRuntimeState

__all__ = [
    # 枚举
    "PluginType",
    "InstallType",
    "RuntimeType",
    "SourceType",
    "TaskStatus",
    "PluginStatus",
    "CredentialScope",
    # 模型
    "PluginConfig",
    "PluginDefaultModel",
    "PluginInstallTask",
    "PluginCredential",
    "PluginRuntimeState",
]
