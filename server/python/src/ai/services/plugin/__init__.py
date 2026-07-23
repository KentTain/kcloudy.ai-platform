"""
插件服务子包

包含插件相关服务：PluginManagementService、PluginConfigService、InstallTaskService 等
"""

from .credential_service import CredentialService, credential_service
from .install_task_service import INSTALL_STEPS, InstallTaskService, install_task_service
from .plugin import PluginManagementService, plugin_management_service
from .plugin_config_provider import (
    PluginConfigProviderImpl,
    plugin_config_provider_impl,
)
from .plugin_config_service import PluginConfigService, plugin_config_service
from .plugin_default_model_service import (
    PluginDefaultModelService,
    plugin_default_model_service,
)
from .plugin_verification_service import (
    PluginVerificationService,
    plugin_verification_service,
)

__all__ = [
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
    "INSTALL_STEPS",
    "CredentialService",
    "credential_service",
    "PluginDefaultModelService",
    "plugin_default_model_service",
]
