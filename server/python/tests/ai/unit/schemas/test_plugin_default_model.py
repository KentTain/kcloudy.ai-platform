"""PluginDefaultModel Schema 测试"""

import pytest

from ai.schemas.plugin_default_model import (
    PluginDefaultModelCreate,
    PluginDefaultModelResponse,
)


class TestPluginDefaultModelSchemas:
    """Schema 测试类"""

    def test_create_schema_standard_model(self):
        """测试创建 Schema（标准模型）"""
        schema = PluginDefaultModelCreate(
            model_type="llm",
            plugin_id="alon/tongyi",
            model_name="qwen-plus",
        )
        assert schema.model_type == "llm"
        assert schema.plugin_id == "alon/tongyi"
        assert schema.model_name == "qwen-plus"

    def test_create_schema_custom_model(self):
        """测试创建 Schema（自定义模型）"""
        schema = PluginDefaultModelCreate(
            model_type="llm",
            plugin_id="openai-api-compatible",
            credential_id="cred-123",
            custom_base_url="https://api.example.com/v1",
            custom_model_name="my-model",
        )
        assert schema.credential_id == "cred-123"
        assert schema.custom_model_name == "my-model"

    def test_response_schema(self):
        """测试响应 Schema"""
        schema = PluginDefaultModelResponse(
            id="test-id",
            tenant_id="tenant-001",
            model_type="llm",
            plugin_id="alon/tongyi",
            model_name="qwen-plus",
            is_valid=True,
        )
        assert schema.id == "test-id"
