"""PluginDefaultModel 模型测试"""

import pytest

from ai.models.plugin import PluginDefaultModel


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

    def test_model_instantiation(self):
        """测试模型实例化，字段赋值正确"""
        instance = PluginDefaultModel(
            model_type="llm",
            plugin_id="langchain",
            tenant_id="tenant-001",
        )
        assert instance.model_type == "llm"
        assert instance.plugin_id == "langchain"
        assert instance.tenant_id == "tenant-001"

    def test_is_valid_default_value(self):
        """测试 is_valid 字段默认值为 True"""
        # SQLAlchemy mapped_column(default=True) 是列级默认值，
        # 在 flush 到数据库时生效，不在 Python __init__ 时生效
        column = PluginDefaultModel.__table__.columns["is_valid"]
        assert column.default is not None
        assert column.default.arg is True
        assert column.nullable is False

    def test_optional_fields_can_be_none(self):
        """测试可选字段默认值为 None"""
        instance = PluginDefaultModel(
            model_type="rerank",
            plugin_id="cohere",
            tenant_id="tenant-001",
        )
        assert instance.model_name is None
        assert instance.credential_id is None
        assert instance.custom_base_url is None
        assert instance.custom_model_name is None
        assert instance.created_by is None
        assert instance.updated_by is None

    def test_mixin_fields_exist(self):
        """验证 TenantMixin 和 AuditMixin 的字段存在"""
        # TenantMixin 字段
        assert hasattr(PluginDefaultModel, "tenant_id")
        # AuditMixin 字段
        assert hasattr(PluginDefaultModel, "created_by")
        assert hasattr(PluginDefaultModel, "updated_by")
        # BaseModel 字段（UUIDPrimaryKeyMixin + TimestampMixin）
        assert hasattr(PluginDefaultModel, "id")
        assert hasattr(PluginDefaultModel, "created_at")
        assert hasattr(PluginDefaultModel, "updated_at")
