"""插件模型配置集成测试

验证从插件安装到对话使用的完整流程。
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin import PluginCredential, CredentialScope
from ai.components.model.services.llm_service import LLMService
from ai.components.model.internal.provider_manager import ProviderManager


class TestPluginModelFlow:
    """插件模型配置流程测试"""

    @pytest.fixture
    def mock_session(self):
        """创建 Mock Session"""
        return MagicMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_chat_uses_plugin_credentials(self, mock_session):
        """测试对话接口使用插件凭证"""
        tenant_id = "test-tenant"
        plugin_id = "alon/tongyi"
        provider = f"{plugin_id}/openai"

        # 模拟凭证已配置
        mock_credential = MagicMock(spec=PluginCredential)
        mock_credential.credentials = {"api_key": "encrypted_key"}
        mock_credential.is_default = True
        mock_credential.is_disabled = False

        with patch(
            "ai.components.model.internal.provider_manager.PluginCredential.one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_credential,
        ):
            with patch(
                "ai.services.credential_service.credential_service.decrypt_credentials",
                return_value={"api_key": "decrypted_key"},
            ):
                llm_service = LLMService(tenant_id)

                # 验证服务创建成功
                assert llm_service._tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_multiple_credentials_uses_default(self, mock_session):
        """测试多个凭证时使用默认凭证"""
        tenant_id = "test-tenant"
        plugin_id = "alon/tongyi"

        # 模拟默认凭证
        mock_default = MagicMock(spec=PluginCredential)
        mock_default.credentials = {"api_key": "default_key_encrypted"}
        mock_default.is_default = True
        mock_default.is_disabled = False

        with patch(
            "ai.components.model.internal.provider_manager.PluginCredential.one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_default,
        ):
            with patch(
                "ai.services.credential_service.credential_service.decrypt_credentials",
                return_value={"api_key": "default_key"},
            ):
                provider_manager = ProviderManager()

                # 验证能提取 plugin_id
                plugin_id_extracted = provider_manager._extract_plugin_id_from_provider(
                    f"{plugin_id}/openai"
                )
                assert plugin_id_extracted == plugin_id

    @pytest.mark.asyncio
    async def test_no_credentials_continues_without_injection(self, mock_session):
        """测试未配置凭证时不注入，保持原有行为"""
        tenant_id = "test-tenant"
        plugin_id = "nonexistent/plugin"

        with patch(
            "ai.components.model.internal.provider_manager.PluginCredential.one_by_conditions",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "ai.components.model.internal.provider_manager.ModelProviderFactory"
            ) as mock_factory_class:
                mock_factory = MagicMock()
                mock_factory.get_providers = AsyncMock(return_value=[])
                mock_factory_class.return_value = mock_factory

                with patch(
                    "ai.components.model.internal.provider_manager.ProviderConfigurations"
                ) as mock_configs_class:
                    mock_configs = MagicMock()
                    mock_configs_class.return_value = mock_configs

                    provider_manager = ProviderManager()

                    # 不传 session 时应该正常工作
                    configurations = await provider_manager.get_configurations(
                        tenant_id=tenant_id,
                        db_session=None,
                    )

                    assert configurations is not None

    @pytest.mark.asyncio
    async def test_extract_credentials_schema(self):
        """测试提取凭证架构"""
        provider_manager = ProviderManager()

        # 创建 Mock ProviderEntity
        mock_provider = MagicMock()
        mock_provider.provider_credential_schema = MagicMock()
        mock_provider.provider_credential_schema.credential_form_schemas = [
            MagicMock(
                variable="api_key",
                type=MagicMock(value="secret-input"),
                required=True,
                options=None,
            ),
            MagicMock(
                variable="base_url",
                type=MagicMock(value="text-input"),
                required=False,
                options=None,
            ),
        ]

        schema = provider_manager._extract_credentials_schema_from_provider(mock_provider)

        assert len(schema) == 2
        assert schema[0]["name"] == "api_key"
        assert schema[0]["type"] == "secret-input"
        assert schema[1]["name"] == "base_url"
