"""PluginDefaultModel 模型测试"""

import pytest

from ai.models.plugin_default_model import PluginDefaultModel


class TestPluginDefaultModel:
    """PluginDefaultModel 测试类"""

    def test_model_class_exists(self):
        """测试模型类存在"""
        assert hasattr(PluginDefaultModel, "__tablename__")
        assert PluginDefaultModel.__tablename__ == "plugin_default_models"

    def test_model_has_required_fields(self):
        """测试模型包含必需字段"""
        assert hasattr(PluginDefaultModel, "model_type")
        assert hasattr(PluginDefaultModel, "plugin_id")
        assert hasattr(PluginDefaultModel, "model_name")
        assert hasattr(PluginDefaultModel, "credential_id")
        assert hasattr(PluginDefaultModel, "custom_base_url")
        assert hasattr(PluginDefaultModel, "custom_model_name")
        assert hasattr(PluginDefaultModel, "is_valid")

    def test_model_inherits_base_model(self):
        """测试模型继承 BaseModel"""
        from ai.models import BaseModel
        assert issubclass(PluginDefaultModel, BaseModel)
