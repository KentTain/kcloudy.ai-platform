"""ProviderManager 重写测试

测试 ProviderManager 的重写功能。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.components.model.internal.provider_manager import ProviderManager
from ai.models.plugin_default_model import PluginDefaultModel


class TestProviderManagerRewrite:
    """ProviderManager 重写测试"""

    @pytest.fixture
    def provider_manager(self):
        return ProviderManager()

    def test_no_deprecated_methods(self, provider_manager):
        """测试不存在废弃方法"""
        assert not hasattr(provider_manager, "_get_all_custom_models")
        assert not hasattr(provider_manager, "_get_all_providers")
        assert not hasattr(provider_manager, "_get_all_provider_model_settings")

    def test_no_get_default_model(self, provider_manager):
        """测试 get_default_model 已删除"""
        assert not hasattr(provider_manager, "get_default_model")

    def test_no_update_default_model_record(self, provider_manager):
        """测试 update_default_model_record 已删除"""
        assert not hasattr(provider_manager, "update_default_model_record")

    def test_no_to_custom_configuration(self, provider_manager):
        """测试 _to_custom_configuration 已删除"""
        assert not hasattr(provider_manager, "_to_custom_configuration")

    def test_no_to_model_settings(self, provider_manager):
        """测试 _to_model_settings 已删除"""
        assert not hasattr(provider_manager, "_to_model_settings")

    @pytest.mark.asyncio
    async def test_get_default_provider_model_name_from_db(self, provider_manager):
        """测试从数据库获取默认模型"""
        mock_session = MagicMock()

        mock_default = MagicMock(spec=PluginDefaultModel)
        mock_default.plugin_id = "alon/tongyi"
        mock_default.model_name = "qwen-plus"
        mock_default.custom_model_name = None

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_default,
        ):
            plugin_id, model_name = await provider_manager.get_default_provider_model_name(
                tenant_id="tenant-001",
                model_type=MagicMock(value="llm"),
                db_session=mock_session,
            )

        assert plugin_id == "alon/tongyi"
        assert model_name == "qwen-plus"

    @pytest.mark.asyncio
    async def test_get_default_provider_model_name_custom_model(self, provider_manager):
        """测试从数据库获取自定义模型名称"""
        mock_session = MagicMock()

        mock_default = MagicMock(spec=PluginDefaultModel)
        mock_default.plugin_id = "alon/custom"
        mock_default.model_name = None
        mock_default.custom_model_name = "my-custom-model"

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_default,
        ):
            plugin_id, model_name = await provider_manager.get_default_provider_model_name(
                tenant_id="tenant-001",
                model_type=MagicMock(value="llm"),
                db_session=mock_session,
            )

        assert plugin_id == "alon/custom"
        assert model_name == "my-custom-model"

    @pytest.mark.asyncio
    async def test_get_default_provider_model_name_fallback(self, provider_manager):
        """测试无默认配置时返回第一个可用模型"""
        mock_session = MagicMock()

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch.object(
                provider_manager,
                "_get_first_provider_first_model",
                new_callable=AsyncMock,
                return_value=("default/plugin", "default-model"),
            ):
                plugin_id, model_name = await provider_manager.get_default_provider_model_name(
                    tenant_id="tenant-001",
                    model_type=MagicMock(value="llm"),
                    db_session=mock_session,
                )

        assert plugin_id == "default/plugin"
        assert model_name == "default-model"

    @pytest.mark.asyncio
    async def test_get_default_provider_model_name_no_session(self, provider_manager):
        """测试无 session 时直接 fallback"""
        with patch.object(
            provider_manager,
            "_get_first_provider_first_model",
            new_callable=AsyncMock,
            return_value=("fallback/plugin", "fallback-model"),
        ):
            plugin_id, model_name = await provider_manager.get_default_provider_model_name(
                tenant_id="tenant-001",
                model_type=MagicMock(value="llm"),
                db_session=None,
            )

        assert plugin_id == "fallback/plugin"
        assert model_name == "fallback-model"

    def test_retained_methods_exist(self, provider_manager):
        """测试保留的方法仍然存在"""
        assert hasattr(provider_manager, "clear_cache")
        assert hasattr(provider_manager, "_get_first_provider_first_model")
        assert hasattr(provider_manager, "_inject_plugin_credentials")
        assert hasattr(provider_manager, "_extract_plugin_id_from_provider")
        assert hasattr(provider_manager, "_extract_credentials_schema_from_provider")
        assert hasattr(provider_manager, "_get_provider_model_bundle")
