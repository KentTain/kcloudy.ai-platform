"""插件市场服务模块"""

from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

__all__ = [
    "MarketplaceAdapter",
    "MarketplaceTestResult",
    "PluginUpdateInfo",
    "RemotePluginInfo",
]
