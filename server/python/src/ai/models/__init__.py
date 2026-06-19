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
from .model_config import ModelConfig, ModelType
from .model_provider import ModelProvider, ProviderType
from .plugin import (
    CredentialScope,
    InstallType,
    Plugin,
    PluginCredential,
    PluginDeclaration,
    PluginInstallation,
    PluginInstallTask,
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
    "ProviderType",
    "ModelType",
    # 插件相关
    "Plugin",
    "PluginDeclaration",
    "PluginInstallation",
    "PluginInstallTask",
    "PluginCredential",
    # 模型提供商相关
    "ModelProvider",
    "ModelConfig",
    # 会话相关
    "ConversationStatus",
    "ConversationMode",
    "MessageStatus",
    "MessageRole",
    "Conversation",
    "Message",
]
