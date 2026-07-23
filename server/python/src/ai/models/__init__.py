"""
AI 模块数据模型

包含 AI 相关的所有模型。
所有模型归属于 ai PostgreSQL schema。
"""

from framework.database import create_base_model, create_module_base

# 创建 AI 模块的 Base 和 BaseModel
Base = create_module_base("ai")
BaseModel = create_base_model(Base)

# 导入枚举（保留在根目录）
from .enums import ConversationMode, ConversationStatus, MessageRole, MessageStatus

# 导入模型（从子目录）
from .conversation import Conversation, Message, MessageMetadata
from .plugin import (
    CredentialScope,
    InstallType,
    PluginConfig,
    PluginCredential,
    PluginDefaultModel,
    PluginInstallTask,
    PluginRuntimeState,
    PluginStatus,
    PluginType,
    RuntimeType,
    SourceType,
    TaskStatus,
)

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
    # 会话相关
    "ConversationStatus",
    "ConversationMode",
    "MessageStatus",
    "MessageRole",
    "Conversation",
    "Message",
    "MessageMetadata",
    # 插件相关
    "PluginConfig",
    "PluginDefaultModel",
    "PluginInstallTask",
    "PluginCredential",
    "PluginRuntimeState",
]
