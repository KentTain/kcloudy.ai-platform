"""模型列表控制器测试"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.controllers.v1.model import router
from ai.schemas.model import ModelListResponse


class TestRouterConfiguration:
    """路由配置测试"""

    def test_router_prefix(self):
        """测试路由前缀"""
        assert router.prefix == "/models"

    def test_router_tags(self):
        """测试路由标签"""
        assert "模型列表" in router.tags


class TestListModels:
    """模型列表测试"""

    @pytest.mark.asyncio
    async def test_list_models_no_tenant(self):
        """测试无租户时返回空列表"""
        with patch("ai.controllers.v1.model.get_tenant_id", return_value=None):
            # 直接导入函数进行测试
            from ai.controllers.v1.model import list_models

            result = await list_models()
            assert isinstance(result, ModelListResponse)
            assert result.providers == []

    @pytest.mark.asyncio
    async def test_list_models_with_tenant(self):
        """测试有租户时返回模型列表"""
        from ai_plugin.sdk.entities.model import ModelType

        # 模拟提供商数据
        mock_provider = MagicMock()
        mock_provider.provider = "openai"
        mock_provider.label = MagicMock()
        mock_provider.label.zh_Hans = "OpenAI"
        mock_provider.label.en_US = "OpenAI"
        mock_provider.models = []
        mock_provider.icon_small = None  # 避免 MagicMock 导致 Pydantic 验证失败
        mock_provider.icon_large = None

        # 模拟模型数据
        mock_model = MagicMock()
        mock_model.model = "gpt-4o-mini"
        mock_model.model_type = ModelType.LLM  # 使用真实的枚举值
        mock_model.label = MagicMock()
        mock_model.label.zh_Hans = "GPT-4o Mini"
        mock_model.label.en_US = "GPT-4o Mini"

        mock_provider.models = [mock_model]

        with (
            patch("ai.controllers.v1.model.get_tenant_id", return_value="test-tenant"),
            patch(
                "ai.controllers.v1.model.ModelProviderFactory"
            ) as mock_factory_class,
        ):
            mock_factory = MagicMock()
            mock_factory.get_providers = AsyncMock(return_value=[mock_provider])
            mock_factory_class.return_value = mock_factory

            from ai.controllers.v1.model import list_models

            result = await list_models()

            assert isinstance(result, ModelListResponse)
            assert len(result.providers) == 1
            assert result.providers[0].id == "openai"
            assert result.providers[0].name == "OpenAI"
            assert len(result.providers[0].models) == 1
            assert result.providers[0].models[0].id == "openai/gpt-4o-mini"
            assert result.providers[0].models[0].name == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_list_models_filters_non_llm(self):
        """测试过滤非 LLM 模型"""
        from ai_plugin.sdk.entities.model import ModelType

        mock_provider = MagicMock()
        mock_provider.provider = "openai"
        mock_provider.label = MagicMock()
        mock_provider.label.zh_Hans = "OpenAI"
        mock_provider.label.en_US = "OpenAI"
        mock_provider.icon_small = None  # 避免 MagicMock 导致 Pydantic 验证失败
        mock_provider.icon_large = None

        # LLM 模型
        llm_model = MagicMock()
        llm_model.model = "gpt-4o-mini"
        llm_model.model_type = ModelType.LLM
        llm_model.label = MagicMock()
        llm_model.label.zh_Hans = "GPT-4o Mini"
        llm_model.label.en_US = "GPT-4o Mini"

        # 嵌入模型
        embedding_model = MagicMock()
        embedding_model.model = "text-embedding-3-small"
        embedding_model.model_type = ModelType.TEXT_EMBEDDING
        embedding_model.label = MagicMock()
        embedding_model.label.zh_Hans = "Text Embedding 3 Small"
        embedding_model.label.en_US = "Text Embedding 3 Small"

        mock_provider.models = [llm_model, embedding_model]

        with (
            patch("ai.controllers.v1.model.get_tenant_id", return_value="test-tenant"),
            patch(
                "ai.controllers.v1.model.ModelProviderFactory"
            ) as mock_factory_class,
        ):
            mock_factory = MagicMock()
            mock_factory.get_providers = AsyncMock(return_value=[mock_provider])
            mock_factory_class.return_value = mock_factory

            from ai.controllers.v1.model import list_models

            result = await list_models()

            # 只有 LLM 模型被返回
            assert len(result.providers[0].models) == 1
            assert result.providers[0].models[0].name == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_list_models_handles_exception(self):
        """测试异常处理"""
        with (
            patch("ai.controllers.v1.model.get_tenant_id", return_value="test-tenant"),
            patch(
                "ai.controllers.v1.model.ModelProviderFactory"
            ) as mock_factory_class,
        ):
            mock_factory = MagicMock()
            mock_factory.get_providers = AsyncMock(side_effect=Exception("Test error"))
            mock_factory_class.return_value = mock_factory

            from ai.controllers.v1.model import list_models

            result = await list_models()

            # 异常时返回空列表
            assert isinstance(result, ModelListResponse)
            assert result.providers == []
