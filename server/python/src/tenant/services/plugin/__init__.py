"""
插件服务子包

包含插件相关服务：PluginDefinitionService、PluginInstallationService、PluginProvider 等
"""

from .plugin_auto_setup_service import (
    PluginAutoSetupService,
    StartupSetupResult,
    plugin_auto_setup_service,
)
from .plugin_definition_service import PluginDefinitionService, plugin_definition_service
from .plugin_installation_service import (
    PluginInstallationService,
    plugin_installation_service,
)
from .plugin_package_service import PluginPackageInfo, PluginPackageService, plugin_package_service
from .plugin_provider import PluginInstallationProviderImpl, plugin_installation_provider_impl
from .plugin_startup_scan_service import (
    StartupScanResult,
    scan_plugins_at_startup,
)
from .plugin_statistics_service import PluginStatisticsService, plugin_statistics_service
from .plugin_storage_service import PluginStorageService, plugin_storage_service

__all__ = [
    "PluginDefinitionService",
    "plugin_definition_service",
    "PluginInstallationService",
    "plugin_installation_service",
    "PluginPackageInfo",
    "PluginPackageService",
    "plugin_package_service",
    "PluginStorageService",
    "plugin_storage_service",
    "PluginStatisticsService",
    "plugin_statistics_service",
    "PluginInstallationProviderImpl",
    "plugin_installation_provider_impl",
    "PluginAutoSetupService",
    "plugin_auto_setup_service",
    "StartupSetupResult",
    "StartupScanResult",
    "scan_plugins_at_startup",
]
