"""测试 PluginConfigProvider 协议注册/获取函数

验证 framework 层提供的依赖倒置注册机制：
- register_plugin_config_provider 注册实现
- get_plugin_config_provider 获取实现
- 未注册时抛出 RuntimeError

注意：全局状态需在测试间清理，避免污染其他测试。
"""

import pytest

from framework.tenant import plugin_protocols
from framework.tenant.plugin_protocols import (
    get_plugin_config_provider,
    register_plugin_config_provider,
)


@pytest.fixture(autouse=True)
def reset_provider():
    """每个测试前后确保全局 _plugin_config_provider 恢复为 None"""
    original = plugin_protocols._plugin_config_provider
    plugin_protocols._plugin_config_provider = None
    yield
    plugin_protocols._plugin_config_provider = original


class TestPluginConfigProviderProtocol:
    """PluginConfigProvider 协议注册测试"""

    def test_register_and_get_provider(self):
        """注册 provider 后 get 能返回同一实例"""
        mock_provider = object()  # 任意对象均可，Protocol 不做运行时校验

        register_plugin_config_provider(mock_provider)

        assert get_plugin_config_provider() is mock_provider

    def test_get_provider_not_registered_raises(self):
        """未注册时 get 抛出 RuntimeError"""
        # reset_provider fixture 已将全局置为 None
        with pytest.raises(RuntimeError) as exc_info:
            get_plugin_config_provider()

        assert "PluginConfigProvider not registered" in str(exc_info.value)
