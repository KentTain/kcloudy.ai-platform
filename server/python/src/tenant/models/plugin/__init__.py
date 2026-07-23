"""
插件定义模型子包

包含插件定义模型：TenantPluginDefinition、TenantPluginInstallation 等
"""

from .plugin_definition import TenantPluginDefinition
from .plugin_installation import TenantPluginInstallation
from .plugin_marketplace import TenantPluginMarketplace
from .plugin_package import TenantPluginPackage

__all__ = [
    "TenantPluginDefinition",
    "TenantPluginInstallation",
    "TenantPluginMarketplace",
    "TenantPluginPackage",
]
