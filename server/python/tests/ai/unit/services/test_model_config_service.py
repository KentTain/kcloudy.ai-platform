"""ModelConfigService 服务测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai.services.model_config_service import ModelConfigService
from ai_plugin.sdk.entities.model import ModelType


class TestModelConfigServiceBatchSetDefault:
    """批量设置默认模型测试"""

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=AsyncSession)

    @pytest.fixture
    def service(self):
        return ModelConfigService()

    async def test_batch_set_llm_default_success(self, service, mock_session):
        """测试设置 LLM 默认模型成功"""
        with patch(
            "ai.services.model_config_service.plugin_default_model_service"
        ) as mock_pdms:
            mock_pdms.get_default_model = AsyncMock(return_value=None)
            mock_pdms.set_default_model = AsyncMock()

            await service.batch_set_default_models(
                mock_session,
                "tenant-001",
                [{"model_type": "llm", "plugin_id": "alon/openai", "model_name": "gpt-4"}],
            )

            mock_pdms.set_default_model.assert_called_once_with(
                session=mock_session,
                tenant_id="tenant-001",
                model_type="llm",
                plugin_id="alon/openai",
                model_name="gpt-4",
            )

    async def test_batch_set_llm_overwrite_existing(self, service, mock_session):
        """测试 LLM 已有默认模型时允许覆盖"""
        mock_existing = MagicMock()
        mock_existing.model_name = "gpt-3.5"

        with patch(
            "ai.services.model_config_service.plugin_default_model_service"
        ) as mock_pdms:
            mock_pdms.get_default_model = AsyncMock(return_value=mock_existing)
            mock_pdms.set_default_model = AsyncMock()

            await service.batch_set_default_models(
                mock_session,
                "tenant-001",
                [{"model_type": "llm", "plugin_id": "alon/openai", "model_name": "gpt-4"}],
            )

            mock_pdms.set_default_model.assert_called_once()

    async def test_batch_set_embedding_rerank_same_plugin(self, service, mock_session):
        """测试 embedding 和 rerank 来自同一插件时设置成功"""
        with patch(
            "ai.services.model_config_service.plugin_default_model_service"
        ) as mock_pdms:
            mock_pdms.get_default_model = AsyncMock(return_value=None)
            mock_pdms.set_default_model = AsyncMock()

            await service.batch_set_default_models(
                mock_session,
                "tenant-001",
                [
                    {
                        "model_type": ModelType.TEXT_EMBEDDING,
                        "plugin_id": "alon/openai",
                        "model_name": "text-embedding-ada",
                    },
                    {
                        "model_type": ModelType.RERANK,
                        "plugin_id": "alon/openai",
                        "model_name": "rerank-v3",
                    },
                ],
            )

            assert mock_pdms.set_default_model.call_count == 2

    async def test_batch_set_embedding_rerank_different_plugin_raises(self, service, mock_session):
        """测试 embedding 和 rerank 来自不同插件时抛出异常"""
        with pytest.raises(ValueError, match="embedding 和 rerank 默认模型必须来自同一插件"):
            await service.batch_set_default_models(
                mock_session,
                "tenant-001",
                [
                    {
                        "model_type": ModelType.TEXT_EMBEDDING,
                        "plugin_id": "alon/openai",
                        "model_name": "text-embedding-ada",
                    },
                    {
                        "model_type": ModelType.RERANK,
                        "plugin_id": "alon/cohere",
                        "model_name": "rerank-v3",
                    },
                ],
            )

    async def test_batch_set_embedding_existing_raises(self, service, mock_session):
        """测试 embedding 已有默认模型时不可覆盖"""
        mock_existing = MagicMock()

        with patch(
            "ai.services.model_config_service.plugin_default_model_service"
        ) as mock_pdms:
            mock_pdms.get_default_model = AsyncMock(return_value=mock_existing)

            with pytest.raises(ValueError, match="类型默认模型设置后不可更改"):
                await service.batch_set_default_models(
                    mock_session,
                    "tenant-001",
                    [
                        {
                            "model_type": ModelType.TEXT_EMBEDDING,
                            "plugin_id": "alon/openai",
                            "model_name": "text-embedding-ada",
                        },
                    ],
                )

    async def test_batch_set_rerank_existing_raises(self, service, mock_session):
        """测试 rerank 已有默认模型时不可覆盖"""
        mock_existing = MagicMock()

        with patch(
            "ai.services.model_config_service.plugin_default_model_service"
        ) as mock_pdms:
            mock_pdms.get_default_model = AsyncMock(return_value=mock_existing)

            with pytest.raises(ValueError, match="类型默认模型设置后不可更改"):
                await service.batch_set_default_models(
                    mock_session,
                    "tenant-001",
                    [
                        {
                            "model_type": ModelType.RERANK,
                            "plugin_id": "alon/cohere",
                            "model_name": "rerank-v3",
                        },
                    ],
                )

    async def test_batch_set_multiple_items(self, service, mock_session):
        """测试批量设置多个非 immutable 类型默认模型"""
        with patch(
            "ai.services.model_config_service.plugin_default_model_service"
        ) as mock_pdms:
            mock_pdms.get_default_model = AsyncMock(return_value=None)
            mock_pdms.set_default_model = AsyncMock()

            await service.batch_set_default_models(
                mock_session,
                "tenant-001",
                [
                    {"model_type": "llm", "plugin_id": "alon/openai", "model_name": "gpt-4"},
                    {"model_type": "tts", "plugin_id": "alon/openai", "model_name": "tts-1"},
                ],
            )

            assert mock_pdms.set_default_model.call_count == 2


class TestModelConfigServiceGetModelsByType:
    """按类型获取可选模型测试"""

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=AsyncSession)

    @pytest.fixture
    def service(self):
        return ModelConfigService()

    async def test_get_models_by_type_filters_correctly(self, service, mock_session):
        """测试按类型筛选模型"""
        mock_provider = MagicMock()
        mock_provider.plugin_id = "alon/openai"
        mock_provider.declaration.provider = "openai"

        mock_model_llm = MagicMock()
        mock_model_llm.model = "gpt-4"
        mock_model_llm.model_type = "llm"
        mock_model_llm.label.zh_Hans = "GPT-4"
        mock_model_llm.label = MagicMock(zh_Hans="GPT-4")

        mock_model_embedding = MagicMock()
        mock_model_embedding.model = "text-embedding-ada"
        mock_model_embedding.model_type = "text-embedding"
        mock_model_embedding.label = MagicMock(zh_Hans="嵌入模型")

        mock_provider.declaration.models = [mock_model_llm, mock_model_embedding]

        with patch(
            "ai.services.model_config_service.ModelProviderFactory"
        ) as mock_factory_cls:
            mock_factory = MagicMock()
            mock_factory.get_plugin_model_providers = AsyncMock(
                return_value=[mock_provider]
            )
            mock_factory_cls.return_value = mock_factory

            result = await service.get_models_by_type(
                mock_session, "tenant-001", "llm"
            )

        assert len(result) == 1
        assert result[0].model_name == "gpt-4"
        assert result[0].model_type == "llm"
        assert result[0].plugin_id == "alon/openai"
        assert result[0].provider == "openai"

    async def test_get_models_by_type_empty(self, service, mock_session):
        """测试无匹配模型返回空列表"""
        with patch(
            "ai.services.model_config_service.ModelProviderFactory"
        ) as mock_factory_cls:
            mock_factory = MagicMock()
            mock_factory.get_plugin_model_providers = AsyncMock(return_value=[])
            mock_factory_cls.return_value = mock_factory

            result = await service.get_models_by_type(
                mock_session, "tenant-001", "llm"
            )

        assert result == []

    async def test_get_models_by_type_provider_exception(self, service, mock_session):
        """测试获取模型提供者失败时返回空列表"""
        with patch(
            "ai.services.model_config_service.ModelProviderFactory"
        ) as mock_factory_cls:
            mock_factory = MagicMock()
            mock_factory.get_plugin_model_providers = AsyncMock(
                side_effect=Exception("connection failed")
            )
            mock_factory_cls.return_value = mock_factory

            result = await service.get_models_by_type(
                mock_session, "tenant-001", "llm"
            )

        assert result == []


class TestModelConfigServiceSetEnabledModels:
    """配置启用模型测试"""

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=AsyncSession)

    @pytest.fixture
    def service(self):
        return ModelConfigService()

    async def test_set_enabled_models_success(self, service, mock_session):
        """测试配置启用模型成功（当前为预留方法）"""
        await service.set_enabled_models(
            mock_session,
            "tenant-001",
            "alon/openai",
            ["gpt-4", "text-embedding-ada"],
        )


class TestModelConfigServiceGetAvailableModels:
    """获取插件可用模型测试"""

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=AsyncSession)

    @pytest.fixture
    def service(self):
        return ModelConfigService()

    async def test_get_available_models_success(self, service, mock_session):
        """测试获取插件可用模型"""
        mock_provider = MagicMock()
        mock_provider.plugin_id = "alon/openai"
        mock_provider.declaration.provider = "openai"

        mock_model = MagicMock()
        mock_model.model = "gpt-4"
        mock_model.model_type = "llm"
        mock_model.label = MagicMock(zh_Hans="GPT-4")

        mock_provider.declaration.models = [mock_model]

        with patch(
            "ai.services.model_config_service.ModelProviderFactory"
        ) as mock_factory_cls:
            mock_factory = MagicMock()
            mock_factory.get_plugin_model_providers = AsyncMock(
                return_value=[mock_provider]
            )
            mock_factory_cls.return_value = mock_factory

            result = await service.get_available_models(
                mock_session, "tenant-001", "alon/openai"
            )

        assert len(result.models) == 1
        assert result.models[0].model_name == "gpt-4"
        assert result.models[0].is_enabled is True

    async def test_get_available_models_other_plugin_excluded(self, service, mock_session):
        """测试其他插件的模型不被返回"""
        mock_provider_a = MagicMock()
        mock_provider_a.plugin_id = "alon/openai"
        mock_provider_a.declaration.models = []

        mock_provider_b = MagicMock()
        mock_provider_b.plugin_id = "alon/cohere"
        mock_model = MagicMock()
        mock_model.model = "rerank-v3"
        mock_model.model_type = "rerank"
        mock_model.label = MagicMock(zh_Hans="Rerank V3")
        mock_provider_b.declaration.models = [mock_model]

        with patch(
            "ai.services.model_config_service.ModelProviderFactory"
        ) as mock_factory_cls:
            mock_factory = MagicMock()
            mock_factory.get_plugin_model_providers = AsyncMock(
                return_value=[mock_provider_a, mock_provider_b]
            )
            mock_factory_cls.return_value = mock_factory

            result = await service.get_available_models(
                mock_session, "tenant-001", "alon/openai"
            )

        assert len(result.models) == 0

    async def test_get_available_models_provider_exception(self, service, mock_session):
        """测试获取模型提供者失败时返回空列表"""
        with patch(
            "ai.services.model_config_service.ModelProviderFactory"
        ) as mock_factory_cls:
            mock_factory = MagicMock()
            mock_factory.get_plugin_model_providers = AsyncMock(
                side_effect=Exception("connection failed")
            )
            mock_factory_cls.return_value = mock_factory

            result = await service.get_available_models(
                mock_session, "tenant-001", "alon/openai"
            )

        assert result.models == []


class TestModelConfigServiceGetOverview:
    """获取模型配置概览测试"""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock(spec=AsyncSession)
        # mock session.execute 返回
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)
        return session

    @pytest.fixture
    def service(self):
        return ModelConfigService()

    async def test_get_overview_no_plugins(self, service, mock_session):
        """测试无模型插件时返回空概览"""
        mock_installation = MagicMock()
        mock_installation.plugin_type = "tool"
        mock_installation.plugin_id = "alon/some-tool"

        with patch(
            "ai.services.model_config_service.get_plugin_installation_provider"
        ) as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.get_tenant_installations = AsyncMock(
                return_value=[mock_installation]
            )
            mock_get_provider.return_value = mock_provider

            result = await service.get_overview(mock_session, "tenant-001")

        assert result.total_plugins == 0
        assert result.configured_plugins == 0
        assert result.total_models == 0
        assert result.plugins == []

    async def test_get_overview_no_installations(self, service, mock_session):
        """测试无安装记录时返回空概览"""
        with patch(
            "ai.services.model_config_service.get_plugin_installation_provider"
        ) as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.get_tenant_installations = AsyncMock(return_value=[])
            mock_get_provider.return_value = mock_provider

            result = await service.get_overview(mock_session, "tenant-001")

        assert result.total_plugins == 0

    async def test_get_overview_with_active_plugin(self, service, mock_session):
        """测试有活跃模型插件时返回正确概览"""
        mock_installation = MagicMock()
        mock_installation.plugin_type = "model"
        mock_installation.plugin_id = "alon/openai"

        mock_provider_entity = MagicMock()
        mock_provider_entity.plugin_id = "alon/openai"

        mock_model_schema = MagicMock()
        mock_model_schema.model = "gpt-4"
        mock_model_schema.model_type = "llm"
        mock_model_schema.label = MagicMock(zh_Hans="GPT-4")

        mock_provider_entity.declaration.models = [mock_model_schema]

        # mock runtime state
        mock_runtime = MagicMock()
        mock_runtime.plugin_id = "alon/openai"
        mock_runtime.status = "active"

        mock_runtime_result = MagicMock()
        mock_runtime_result.scalars.return_value.all.return_value = [mock_runtime]

        mock_default_result = MagicMock()
        mock_default_result.scalars.return_value.all.return_value = []

        # 两次 session.execute 分别返回 runtime 和 default
        mock_session.execute = AsyncMock(
            side_effect=[mock_runtime_result, mock_default_result]
        )

        with patch(
            "ai.services.model_config_service.get_plugin_installation_provider"
        ) as mock_get_provider, patch(
            "ai.services.model_config_service.ModelProviderFactory"
        ) as mock_factory_cls:
            mock_provider = MagicMock()
            mock_provider.get_tenant_installations = AsyncMock(
                return_value=[mock_installation]
            )
            mock_get_provider.return_value = mock_provider

            mock_factory = MagicMock()
            mock_factory.get_plugin_model_providers = AsyncMock(
                return_value=[mock_provider_entity]
            )
            mock_factory_cls.return_value = mock_factory

            result = await service.get_overview(mock_session, "tenant-001")

        assert result.total_plugins == 1
        assert result.configured_plugins == 1
        assert result.total_models == 1
        assert len(result.plugins) == 1
        assert result.plugins[0].plugin_id == "alon/openai"
        assert result.plugins[0].status == "active"
        assert len(result.plugins[0].models) == 1
        assert result.plugins[0].models[0].model_name == "gpt-4"

    async def test_get_overview_inactive_plugin_excluded(self, service, mock_session):
        """测试未启动的插件不在返回列表中"""
        mock_installation = MagicMock()
        mock_installation.plugin_type = "model"
        mock_installation.plugin_id = "alon/openai"

        mock_provider_entity = MagicMock()
        mock_provider_entity.plugin_id = "alon/openai"

        mock_model_schema = MagicMock()
        mock_model_schema.model = "gpt-4"
        mock_model_schema.model_type = "llm"
        mock_model_schema.label = MagicMock(zh_Hans="GPT-4")

        mock_provider_entity.declaration.models = [mock_model_schema]

        # mock runtime state: inactive
        mock_runtime = MagicMock()
        mock_runtime.plugin_id = "alon/openai"
        mock_runtime.status = "inactive"

        mock_runtime_result = MagicMock()
        mock_runtime_result.scalars.return_value.all.return_value = [mock_runtime]

        mock_default_result = MagicMock()
        mock_default_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[mock_runtime_result, mock_default_result]
        )

        with patch(
            "ai.services.model_config_service.get_plugin_installation_provider"
        ) as mock_get_provider, patch(
            "ai.services.model_config_service.ModelProviderFactory"
        ) as mock_factory_cls:
            mock_provider = MagicMock()
            mock_provider.get_tenant_installations = AsyncMock(
                return_value=[mock_installation]
            )
            mock_get_provider.return_value = mock_provider

            mock_factory = MagicMock()
            mock_factory.get_plugin_model_providers = AsyncMock(
                return_value=[mock_provider_entity]
            )
            mock_factory_cls.return_value = mock_factory

            result = await service.get_overview(mock_session, "tenant-001")

        # configured_plugins 统计了，但 plugins 列表为空（因为 inactive）
        assert result.configured_plugins == 1
        assert result.plugins == []
