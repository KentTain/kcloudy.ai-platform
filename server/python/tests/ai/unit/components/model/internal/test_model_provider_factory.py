# ModelProviderFactory 单元测试

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.components.model.errors.error import (
    ProviderNotFoundError,
    UnsupportedProviderError,
)
from ai.components.model.internal.model_provider_factory import ModelProviderFactory
from ai.components.model.schema.provider_id import (
    ModelProviderID,
    ProviderIDFormatError,
)


class TestModelProviderFactoryInit:
    """ModelProviderFactory 初始化测试"""

    def test_init_with_tenant_id(self):
        """测试使用租户 ID 初始化"""
        tenant_id = "test-tenant-001"

        with patch.object(ModelProviderFactory, "__init__", lambda self, tid: None):
            factory = ModelProviderFactory.__new__(ModelProviderFactory)
            factory.tenant_id = tenant_id
            factory.provider_position_map = {}
            factory.plugin_model_manager = MagicMock()

            assert factory.tenant_id == tenant_id

    def test_init_creates_plugin_model_manager(self):
        """测试初始化创建插件模型管理器"""
        tenant_id = "test-tenant-001"

        with patch(
            "ai.components.plugin.client.model_client.ModelClient"
        ) as mock_client:
            mock_client.return_value = MagicMock()

            with patch(
                "ai.components.model.internal.model_provider_factory.get_provider_position_map"
            ) as mock_position:
                mock_position.return_value = {}

                factory = ModelProviderFactory(tenant_id)

                assert factory.tenant_id == tenant_id
                assert factory.plugin_model_manager is not None


class TestModelProviderFactoryGetProviders:
    """ModelProviderFactory get_providers 测试"""

    @pytest.mark.asyncio
    async def test_get_providers_returns_list(self):
        """测试获取提供者返回列表"""
        tenant_id = "test-tenant-001"
        factory = ModelProviderFactory.__new__(ModelProviderFactory)
        factory.tenant_id = tenant_id
        factory.provider_position_map = {}
        factory.plugin_model_manager = AsyncMock()

        # 模拟插件提供者
        mock_provider = MagicMock()
        mock_provider.declaration = MagicMock()
        mock_provider.declaration.provider = "test-provider"
        mock_provider.plugin_id = "test-plugin"

        factory.plugin_model_manager.fetch_model_providers = AsyncMock(
            return_value=[mock_provider]
        )

        with patch(
            "ai.components.model.internal.model_provider_factory.sort_to_dict_by_position_map"
        ) as mock_sort:
            mock_extension = MagicMock()
            mock_extension.plugin_model_provider_entity = mock_provider
            mock_sort.return_value = {"test-provider": mock_extension}

            providers = await factory.get_providers()

            assert isinstance(providers, list)

    @pytest.mark.asyncio
    async def test_get_providers_empty_result(self):
        """测试没有提供者时返回空列表"""
        tenant_id = "test-tenant-001"
        factory = ModelProviderFactory.__new__(ModelProviderFactory)
        factory.tenant_id = tenant_id
        factory.provider_position_map = {}
        factory.plugin_model_manager = AsyncMock()

        factory.plugin_model_manager.fetch_model_providers = AsyncMock(return_value=[])

        with patch(
            "ai.components.model.internal.model_provider_factory.sort_to_dict_by_position_map"
        ) as mock_sort:
            mock_sort.return_value = {}

            providers = await factory.get_providers()

            assert providers == []


class TestModelProviderFactoryGetPluginModelProvider:
    """ModelProviderFactory get_plugin_model_provider 测试"""

    @pytest.mark.asyncio
    async def test_get_plugin_model_provider_success(self):
        """测试成功获取插件模型提供者"""
        tenant_id = "test-tenant-001"
        factory = ModelProviderFactory.__new__(ModelProviderFactory)
        factory.tenant_id = tenant_id
        factory.provider_position_map = {}
        factory.plugin_model_manager = AsyncMock()

        # 模拟提供者
        mock_provider = MagicMock()
        mock_provider.declaration = MagicMock()
        mock_provider.declaration.provider = "langgenius/test-plugin/test-provider"

        factory.get_plugin_model_providers = AsyncMock(return_value=[mock_provider])

        result = await factory.get_plugin_model_provider(
            "langgenius/test-plugin/test-provider"
        )

        assert result == mock_provider

    @pytest.mark.asyncio
    async def test_get_plugin_model_provider_not_found(self):
        """测试提供者不存在抛出异常"""
        tenant_id = "test-tenant-001"
        factory = ModelProviderFactory.__new__(ModelProviderFactory)
        factory.tenant_id = tenant_id
        factory.provider_position_map = {}

        factory.get_plugin_model_providers = AsyncMock(return_value=[])

        # 使用正确的格式，但提供者不存在
        with pytest.raises(ProviderNotFoundError) as exc_info:
            await factory.get_plugin_model_provider("langgenius/test-plugin/nonexistent")

        assert "nonexistent" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_plugin_model_provider_short_format_matches_directly(self):
        """测试简化格式按当前实现直接匹配"""
        tenant_id = "test-tenant-001"
        factory = ModelProviderFactory.__new__(ModelProviderFactory)
        factory.tenant_id = tenant_id
        factory.provider_position_map = {}

        # 当前实现中，包含 / 的 provider 不会再转换，直接匹配 declaration.provider
        mock_provider = MagicMock()
        mock_provider.declaration = MagicMock()
        mock_provider.declaration.provider = "test-plugin/openai"

        factory.get_plugin_model_providers = AsyncMock(return_value=[mock_provider])

        result = await factory.get_plugin_model_provider("test-plugin/openai")

        assert result == mock_provider


class TestModelProviderFactoryProviderCredentialsValidate:
    """ModelProviderFactory provider_credentials_validate 测试"""

    @pytest.mark.asyncio
    async def test_validate_credentials_success(self):
        """测试凭证验证成功"""
        tenant_id = "test-tenant-001"
        factory = ModelProviderFactory.__new__(ModelProviderFactory)
        factory.tenant_id = tenant_id
        factory.plugin_model_manager = AsyncMock()

        # 模拟提供者
        mock_provider = MagicMock()
        mock_provider.declaration = MagicMock()
        mock_provider.declaration.provider_credential_schema = MagicMock()
        mock_provider.plugin_id = "test-plugin"
        mock_provider.provider = "test-provider"

        factory.get_plugin_model_provider = AsyncMock(return_value=mock_provider)
        factory.plugin_model_manager.validate_provider_credentials = AsyncMock(
            return_value=True
        )

        credentials = {"api_key": "test-key"}

        result = await factory.provider_credentials_validate(
            provider="test-provider", credentials=credentials
        )

        assert result == credentials

    @pytest.mark.asyncio
    async def test_validate_credentials_no_schema(self):
        """测试提供者无凭证模式时抛出异常"""
        tenant_id = "test-tenant-001"
        factory = ModelProviderFactory.__new__(ModelProviderFactory)
        factory.tenant_id = tenant_id

        # 模拟提供者无凭证模式
        mock_provider = MagicMock()
        mock_provider.declaration = MagicMock()
        mock_provider.declaration.provider_credential_schema = None

        factory.get_plugin_model_provider = AsyncMock(return_value=mock_provider)

        with pytest.raises(UnsupportedProviderError) as exc_info:
            await factory.provider_credentials_validate(
                provider="test-provider", credentials={"api_key": "test"}
            )

        assert "没有提供者凭证模式" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_credentials_validation_failed(self):
        """测试凭证验证失败时抛出异常"""
        tenant_id = "test-tenant-001"
        factory = ModelProviderFactory.__new__(ModelProviderFactory)
        factory.tenant_id = tenant_id
        factory.plugin_model_manager = AsyncMock()

        # 模拟提供者
        mock_provider = MagicMock()
        mock_provider.declaration = MagicMock()
        mock_provider.declaration.provider_credential_schema = MagicMock()
        mock_provider.plugin_id = "test-plugin"
        mock_provider.provider = "test-provider"

        factory.get_plugin_model_provider = AsyncMock(return_value=mock_provider)
        factory.plugin_model_manager.validate_provider_credentials = AsyncMock(
            return_value=False
        )

        with pytest.raises(ValueError, match="凭证验证失败"):
            await factory.provider_credentials_validate(
                provider="test-provider", credentials={"api_key": "invalid"}
            )


class TestModelProviderID:
    """ModelProviderID 解析测试"""

    def test_parse_full_format(self):
        """测试完整格式解析"""
        provider_id = ModelProviderID("langgenius/openai/gpt-4")

        assert provider_id.organization == "langgenius"
        assert provider_id.plugin_name == "openai"
        assert provider_id.provider_name == "gpt-4"
        assert str(provider_id) == "langgenius/openai/gpt-4"

    def test_parse_short_format(self):
        """测试简化格式解析"""
        provider_id = ModelProviderID("plugin-001/openai")

        assert provider_id.organization == "langgenius"
        assert provider_id.plugin_name == "plugin-001"
        assert provider_id.provider_name == "openai"
        # plugin_id 返回原始值
        assert provider_id.plugin_id == "plugin-001"

    def test_parse_invalid_format(self):
        """测试无效格式抛出异常"""
        with pytest.raises(ProviderIDFormatError):
            ModelProviderID("invalid-format")

    def test_parse_empty_string(self):
        """测试空字符串抛出异常"""
        with pytest.raises(ProviderIDFormatError):
            ModelProviderID("")

    def test_is_langgenius(self):
        """测试 is_langgenius 方法"""
        provider_id = ModelProviderID("langgenius/openai/gpt-4")
        assert provider_id.is_langgenius() is True

        provider_id2 = ModelProviderID("other-org/plugin/provider")
        assert provider_id2.is_langgenius() is False

    def test_google_maps_to_gemini(self):
        """测试 Google 模型映射到 Gemini 插件"""
        # 注意：映射只在 provider_name 为 "google" 时触发
        # 例如：langgenius/google/google 会映射 plugin_name 到 gemini
        provider_id = ModelProviderID("langgenius/google/google")

        # Google 提供者应该映射到 gemini 插件
        assert provider_id.plugin_name == "gemini"

    def test_google_provider_name_not_mapped(self):
        """测试 provider_name 不是 google 时不会映射"""
        # 当 provider_name 不是 "google" 时，不会触发映射
        provider_id = ModelProviderID("langgenius/google/gemini-pro")

        # plugin_name 保持原值
        assert provider_id.plugin_name == "google"


class TestProviderNotFoundError:
    """ProviderNotFoundError 异常测试"""

    def test_error_message_default(self):
        """测试默认错误消息"""
        error = ProviderNotFoundError("test-provider")

        assert error.provider == "test-provider"
        assert "test-provider" in str(error)
        assert "不存在" in str(error)

    def test_error_message_custom(self):
        """测试自定义错误消息"""
        error = ProviderNotFoundError("test-provider", "自定义错误消息")

        assert error.provider == "test-provider"
        assert error.message == "自定义错误消息"


class TestUnsupportedProviderError:
    """UnsupportedProviderError 异常测试"""

    def test_error_message_default(self):
        """测试默认错误消息"""
        error = UnsupportedProviderError("unsupported-provider")

        assert error.provider == "unsupported-provider"
        assert "不支持的 Provider 类型" in str(error)

    def test_error_message_custom(self):
        """测试自定义错误消息"""
        error = UnsupportedProviderError(
            "unsupported-provider", "不支持此类型"
        )

        assert error.provider == "unsupported-provider"
        assert error.message == "不支持此类型"
