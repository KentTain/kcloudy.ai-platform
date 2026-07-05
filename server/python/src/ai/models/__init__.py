"""
AI 模块数据模型

包含 AI 相关的所有模型。
所有模型归属于 ai PostgreSQL schema。
"""

from framework.database import create_base_model, create_module_base

# 创建 AI 模块的 Base 和 BaseModel
Base = create_module_base("ai")
BaseModel = create_base_model(Base)

# 导入模型（必须在 Base 和 BaseModel 定义之后）
from .conversation import Conversation
from .enums import ConversationMode, ConversationStatus, MessageRole, MessageStatus
from .message import Message
from .message_metadata import MessageMetadata
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
    # Base
    "Base",
    "BaseModel",
    # 枚举
    "PluginType",
    "InstallType",
    "RuntimeType",
    "SourceType",
    "TaskStatus",
    "PluginStatus",
    "CredentialScope",
    # 插件相关
    "PluginConfig",
    "PluginDefaultModel",
    "PluginInstallTask",
    "PluginCredential",
    "PluginRuntimeState",
    # 会话相关
    "ConversationStatus",
    "ConversationMode",
    "MessageStatus",
    "MessageRole",
    "Conversation",
    "Message",
    "MessageMetadata",
]
