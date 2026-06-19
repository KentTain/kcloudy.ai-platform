# ModelInstanceFactory 单元测试

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.components.model.internal.model_instance_factory import ModelInstanceFactory
from ai.components.model.errors.error import (
    ModelInvocationError,
    ModelCredentialError,
    ProviderNotFoundError,
)
from ai.models.model_config import ModelType


class TestModelInstanceFactoryInit:
    """ModelInstanceFactory 初始化测试"""

    def test_init_creates_provider_manager(self):
        """测试初始化创建 ProviderManager"""
        with patch(
            "ai.components.model.internal.model_instance_factory.ProviderManager"
        ) as mock_pm:
            mock_pm.return_value = MagicMock()

            factory = ModelInstanceFactory()

            assert factory._provider_manager is not None


class TestModelInstanceFactoryGetModelInstance:
    """ModelInstanceFactory get_model_instance 测试"""

    @pytest.mark.asyncio
    async def test_get_model_instance_success(self):
        """测试成功获取模型实例"""
        factory = ModelInstanceFactory.__new__(ModelInstanceFactory)
        factory._provider_manager = AsyncMock()

        # 模拟 ProviderModelBundle
        mock_bundle = MagicMock()
        mock_bundle.provider_model_instance = MagicMock()
        mock_bundle.model_schema = MagicMock()

        factory._provider_manager._get_provider_model_bundle = AsyncMock(
            return_value=mock_bundle
        )

        with patch(
            "ai.components.model.internal.model_instance_factory.ModelInstance"
        ) as mock_instance_class:
            mock_instance = MagicMock()
            mock_instance_class.return_value = mock_instance

            result = await factory.get_model_instance(
                tenant_id="test-tenant",
                provider="openai",
                model_type=ModelType.LLM,
                model="gpt-4",
            )

            assert result == mock_instance
            factory._provider_manager._get_provider_model_bundle.assert_called_once_with(
                tenant_id="test-tenant",
                provider="openai",
                model_type=ModelType.LLM,
            )

    @pytest.mark.asyncio
    async def test_get_model_instance_provider_not_found(self):
        """测试提供者不存在时抛出异常"""
        factory = ModelInstanceFactory.__new__(ModelInstanceFactory)
        factory._provider_manager = AsyncMock()

        factory._provider_manager._get_provider_model_bundle = AsyncMock(
            side_effect=ProviderNotFoundError("openai")
        )

        with pytest.raises(ProviderNotFoundError):
            await factory.get_model_instance(
                tenant_id="test-tenant",
                provider="nonexistent",
                model_type=ModelType.LLM,
                model="gpt-4",
            )

    @pytest.mark.asyncio
    async def test_get_model_instance_credential_error(self):
        """测试凭证错误时抛出异常"""
        factory = ModelInstanceFactory.__new__(ModelInstanceFactory)
        factory._provider_manager = AsyncMock()

        factory._provider_manager._get_provider_model_bundle = AsyncMock(
            side_effect=ModelCredentialError("凭证无效", provider="openai")
        )

        with pytest.raises(ModelCredentialError):
            await factory.get_model_instance(
                tenant_id="test-tenant",
                provider="openai",
                model_type=ModelType.LLM,
                model="gpt-4",
            )


class TestModelInstanceFactoryGetDefaultProviderModelName:
    """ModelInstanceFactory get_default_provider_model_name 测试"""

    @pytest.mark.asyncio
    async def test_get_default_provider_model_name_success(self):
        """测试获取默认提供者和模型名称"""
        factory = ModelInstanceFactory.__new__(ModelInstanceFactory)
        factory._provider_manager = AsyncMock()

        factory._provider_manager.get_default_provider_model_name = AsyncMock(
            return_value=("openai", "gpt-4")
        )

        provider, model = await factory.get_default_provider_model_name(
            tenant_id="test-tenant",
            model_type=ModelType.LLM,
        )

        assert provider == "openai"
        assert model == "gpt-4"

    @pytest.mark.asyncio
    async def test_get_default_provider_model_name_none(self):
        """测试没有默认配置时返回 None"""
        factory = ModelInstanceFactory.__new__(ModelInstanceFactory)
        factory._provider_manager = AsyncMock()

        factory._provider_manager.get_default_provider_model_name = AsyncMock(
            return_value=(None, None)
        )

        provider, model = await factory.get_default_provider_model_name(
            tenant_id="test-tenant",
            model_type=ModelType.LLM,
        )

        assert provider is None
        assert model is None

    @pytest.mark.asyncio
    async def test_get_default_provider_model_name_different_types(self):
        """测试不同模型类型获取默认配置"""
        factory = ModelInstanceFactory.__new__(ModelInstanceFactory)
        factory._provider_manager = AsyncMock()

        # 设置不同模型类型的默认值
        async def mock_default(tenant_id, model_type):
            if model_type == ModelType.LLM:
                return ("openai", "gpt-4")
            elif model_type == ModelType.TEXT_EMBEDDING:
                return ("openai", "text-embedding-3")
            return (None, None)

        factory._provider_manager.get_default_provider_model_name = mock_default

        # 测试 LLM 类型
        provider, model = await factory.get_default_provider_model_name(
            tenant_id="test-tenant",
            model_type=ModelType.LLM,
        )
        assert provider == "openai"
        assert model == "gpt-4"

        # 测试 TEXT_EMBEDDING 类型
        provider, model = await factory.get_default_provider_model_name(
            tenant_id="test-tenant",
            model_type=ModelType.TEXT_EMBEDDING,
        )
        assert provider == "openai"
        assert model == "text-embedding-3"


class TestModelInstanceFactoryGetDefaultModelInstance:
    """ModelInstanceFactory get_default_model_instance 测试"""

    @pytest.mark.asyncio
    async def test_get_default_model_instance_success(self):
        """测试获取默认模型实例"""
        factory = ModelInstanceFactory.__new__(ModelInstanceFactory)
        factory._provider_manager = AsyncMock()

        # 模拟默认配置
        factory._provider_manager.get_default_provider_model_name = AsyncMock(
            return_value=("openai", "gpt-4")
        )

        # 模拟 ProviderModelBundle
        mock_bundle = MagicMock()
        factory._provider_manager._get_provider_model_bundle = AsyncMock(
            return_value=mock_bundle
        )

        with patch(
            "ai.components.model.internal.model_instance_factory.ModelInstance"
        ) as mock_instance_class:
            mock_instance = MagicMock()
            mock_instance_class.return_value = mock_instance

            result = await factory.get_default_model_instance(
                tenant_id="test-tenant",
                model_type=ModelType.LLM,
            )

            assert result == mock_instance

    @pytest.mark.asyncio
    async def test_get_default_model_instance_no_default(self):
        """测试没有默认模型时抛出异常"""
        factory = ModelInstanceFactory.__new__(ModelInstanceFactory)
        factory._provider_manager = AsyncMock()

        # 模拟没有默认配置
        factory._provider_manager.get_default_provider_model_name = AsyncMock(
            return_value=(None, None)
        )

        with pytest.raises(ValueError, match="没有为 .* 类型配置默认模型"):
            await factory.get_default_model_instance(
                tenant_id="test-tenant",
                model_type=ModelType.LLM,
            )


class TestModelTypeEnum:
    """ModelType 枚举测试"""

    def test_model_type_values(self):
        """测试模型类型枚举值"""
        assert ModelType.LLM == "llm"
        assert ModelType.TEXT_EMBEDDING == "text-embedding"
        assert ModelType.RERANK == "rerank"
        assert ModelType.SPEECH2TEXT == "speech2text"
        assert ModelType.TTS == "tts"
        assert ModelType.MODERATION == "moderation"

    def test_model_type_string_conversion(self):
        """测试模型类型字符串转换"""
        # 枚举的 str() 返回 "ModelType.LLM"，使用 .value 获取 "llm"
        assert ModelType.LLM.value == "llm"

    def test_model_type_from_string(self):
        """测试从字符串创建模型类型"""
        model_type = ModelType("llm")
        assert model_type == ModelType.LLM

        model_type = ModelType("text-embedding")
        assert model_type == ModelType.TEXT_EMBEDDING


class TestModelInvocationError:
    """ModelInvocationError 异常测试"""

    def test_error_message_default(self):
        """测试默认错误消息"""
        error = ModelInvocationError()

        assert error.message == "模型调用失败"
        assert str(error) == "模型调用失败"

    def test_error_message_custom(self):
        """测试自定义错误消息"""
        error = ModelInvocationError("自定义错误消息")

        assert error.message == "自定义错误消息"

    def test_error_with_original(self):
        """测试包含原始异常"""
        original = ValueError("原始错误")
        error = ModelInvocationError("调用失败", original_error=original)

        assert error.original_error == original


class TestModelCredentialError:
    """ModelCredentialError 异常测试"""

    def test_error_message_default(self):
        """测试默认错误消息"""
        error = ModelCredentialError()

        assert error.message == "模型凭证无效"
        assert error.provider is None

    def test_error_with_provider(self):
        """测试包含提供者信息"""
        error = ModelCredentialError("凭证无效", provider="openai")

        assert error.message == "凭证无效"
        assert error.provider == "openai"
