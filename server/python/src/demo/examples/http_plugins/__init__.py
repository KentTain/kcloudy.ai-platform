"""
HTTP 插件示例模块

本模块演示 HTTP 插件开发：
- 天气查询插件
- 错误处理与重试机制
- Mock 数据支持
- LangChain 工具集成

示例使用：
    from demo.examples.http_plugins import WeatherPlugin, MockWeatherClient
"""

from demo.examples.http_plugins.weather_plugin_demo import (
    HTTPClient,
    MockWeatherClient,
    WeatherPlugin,
    WeatherPluginDemo,
)
from demo.examples.http_plugins.error_handling_demo import (
    RetryConfig,
    RetryableHTTPClient,
    error_handling_demo,
)
from demo.examples.http_plugins.mock_data_demo import (
    MockDataConfig,
    MockDataProvider,
    mock_data_demo,
)

__all__ = [
    "HTTPClient",
    "MockWeatherClient",
    "WeatherPlugin",
    "WeatherPluginDemo",
    "RetryConfig",
    "RetryableHTTPClient",
    "error_handling_demo",
    "MockDataConfig",
    "MockDataProvider",
    "mock_data_demo",
]
