"""
AI 模块服务层

包含插件管理、凭证管理等业务逻辑服务。
"""

from ai.services.credential_service import CredentialService, credential_service
from ai.services.plugin import PluginManagementService, plugin_management_service

__all__ = [
    # 凭证服务
    "CredentialService",
    "credential_service",
    # 插件管理服务
    "PluginManagementService",
    "plugin_management_service",
]
