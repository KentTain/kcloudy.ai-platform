"""PluginCredential 模型测试"""

import pytest

from ai.models.plugin import PluginCredential, CredentialScope


class TestPluginCredential:
    """PluginCredential 测试类"""

    def test_is_default_field_exists(self):
        """测试 is_default 字段存在且默认为 False"""
        # 验证字段定义
        assert hasattr(PluginCredential, "is_default")
        # 获取列对象验证默认值
        column = PluginCredential.__table__.c.is_default
        assert column.default.arg is False

    def test_is_default_can_be_true(self):
        """测试 is_default 可以设置为 True"""
        credential = PluginCredential(
            tenant_id="test-tenant",
            plugin_id="test/plugin",
            plugin_type="model",
            scope=CredentialScope.GLOBAL,
            name="测试凭证",
            credentials={"api_key": "test"},
            is_default=True,
        )
        assert credential.is_default is True
