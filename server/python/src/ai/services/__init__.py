"""
AI 模块服务层

包含插件管理、凭证管理、会话管理、聊天等业务逻辑服务。
"""

from .conversation import (
    ChatService,
    ConversationService,
    FeedbackService,
    chat_service,
    conversation_service,
    feedback_service,
)
from .model import ModelConfigService, model_config_service
from .plugin import (
    CredentialService,
    InstallTaskService,
    PluginConfigProviderImpl,
    PluginConfigService,
    PluginDefaultModelService,
    PluginManagementService,
    PluginVerificationService,
    credential_service,
    install_task_service,
    plugin_config_provider_impl,
    plugin_config_service,
    plugin_default_model_service,
    plugin_management_service,
    plugin_verification_service,
)

__all__ = [
    # 会话服务
    "ChatService",
    "chat_service",
    "ConversationService",
    "conversation_service",
    "FeedbackService",
    "feedback_service",
    # 模型服务
    "ModelConfigService",
    "model_config_service",
    # 插件服务
    "PluginManagementService",
    "plugin_management_service",
    "PluginConfigService",
    "plugin_config_service",
    "PluginConfigProviderImpl",
    "plugin_config_provider_impl",
    "PluginVerificationService",
    "plugin_verification_service",
    "InstallTaskService",
    "install_task_service",
    "CredentialService",
    "credential_service",
    "PluginDefaultModelService",
    "plugin_default_model_service",
]
