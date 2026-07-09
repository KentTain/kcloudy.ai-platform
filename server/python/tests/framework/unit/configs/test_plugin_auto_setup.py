"""插件自动设置配置模型测试"""

import pytest
from framework.configs.plugin_auto_setup import (
    PluginAutoSetupItem,
    VerificationConfig,
    PluginAutoSetupConfig,
)


def test_verification_config_defaults():
    """测试验证配置默认值"""
    config = VerificationConfig()

    assert config.enabled is True
    assert config.timeout == 10
    assert config.on_failure == "warn"


def test_verification_config_custom_values():
    """测试验证配置自定义值"""
    config = VerificationConfig(
        enabled=False,
        timeout=30,
        on_failure="degrade"
    )

    assert config.enabled is False
    assert config.timeout == 30
    assert config.on_failure == "degrade"


def test_verification_config_invalid_timeout():
    """测试验证配置超时时间校验"""
    with pytest.raises(ValueError):
        VerificationConfig(timeout=0)

    with pytest.raises(ValueError):
        VerificationConfig(timeout=100)


def test_verification_config_invalid_strategy():
    """测试验证配置失败策略校验"""
    with pytest.raises(ValueError):
        VerificationConfig(on_failure="invalid")


def test_plugin_auto_setup_item_defaults():
    """测试插件自动设置项默认值"""
    item = PluginAutoSetupItem(plugin_id="test-plugin")

    assert item.plugin_id == "test-plugin"
    assert item.auto_install is True
    assert item.auto_start is True
    assert item.credentials == {}


def test_plugin_auto_setup_item_with_credentials():
    """测试插件自动设置项包含凭证"""
    item = PluginAutoSetupItem(
        plugin_id="langgenius-tongyi",
        auto_install=True,
        auto_start=True,
        credentials={
            "api_key": "sk-test-key",
            "endpoint": "https://api.example.com"
        }
    )

    assert item.plugin_id == "langgenius-tongyi"
    assert item.credentials["api_key"] == "sk-test-key"
    assert item.credentials["endpoint"] == "https://api.example.com"


def test_plugin_auto_setup_config_defaults():
    """测试插件自动设置总配置默认值"""
    config = PluginAutoSetupConfig()

    assert config.enabled is False
    assert config.plugins == []
    assert config.verification.enabled is True


def test_plugin_auto_setup_config_full():
    """测试插件自动设置总配置完整示例"""
    config = PluginAutoSetupConfig(
        enabled=True,
        plugins=[
            PluginAutoSetupItem(
                plugin_id="langgenius-tongyi",
                credentials={"api_key": "test-key"}
            )
        ],
        verification=VerificationConfig(
            enabled=True,
            timeout=15,
            on_failure="degrade"
        )
    )

    assert config.enabled is True
    assert len(config.plugins) == 1
    assert config.plugins[0].plugin_id == "langgenius-tongyi"
    assert config.verification.timeout == 15
