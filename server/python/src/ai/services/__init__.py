"""
AI 模块服务层

包含插件管理、凭证管理、会话管理、聊天等业务逻辑服务。
"""

from ai.services.chat_service import ChatService, chat_service
from ai.services.conversation_service import ConversationService, conversation_service
from ai.services.credential_service import CredentialService, credential_service
from ai.services.install_task_service import InstallTaskService, install_task_service
from ai.services.plugin import PluginManagementService, plugin_management_service

__all__ = [
    # 聊天服务
    "ChatService",
    "chat_service",
    # 会话服务
    "ConversationService",
    "conversation_service",
    # 凭证服务
    "CredentialService",
    "credential_service",
    # 插件管理服务
    "PluginManagementService",
    "plugin_management_service",
    # 安装任务服务
    "InstallTaskService",
    "install_task_service",
]
