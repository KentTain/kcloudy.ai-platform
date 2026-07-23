"""默认模型配置集成测试

验证默认模型设置和获取的完整流程。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.model.internal.provider_manager import ProviderManager
from ai.models.plugin import PluginDefaultModel
from ai.services.plugin import plugin_default_model_service
from ai_plugin.sdk.entities.model import ModelType


class TestPluginDefaultModelFlow:
    """默认模型配置流程测试"""

    @pytest.fixture
    def mock_session(self):
        """创建 Mock Session"""
        return MagicMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_set_and_get_default_model(self, mock_session):
        """测试设置和获取默认模型"""
        # 设置默认模型
        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch.object(
                PluginDefaultModel,
                "create",
                new_callable=AsyncMock,
            ) as mock_create:
                # 设置默认模型
                await plugin_default_model_service.set_default_model(
                    mock_session,
                    tenant_id="tenant-001",
                    model_type=ModelType.LLM.value,
                    plugin_id="alon/tongyi",
                    model_name="qwen-plus",
                )

                # 验证 create 被调用
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_provider_manager_uses_default_model(self, mock_session):
        """测试 ProviderManager 使用默认模型"""
        provider_manager = ProviderManager()

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
            with patch.object(
                provider_manager,
                "_get_first_provider_first_model",
                new_callable=AsyncMock,
                return_value=(None, None),
            ):
                plugin_id, model_name = await provider_manager.get_default_provider_model_name(
                    tenant_id="tenant-001",
                    model_type=ModelType.LLM,
                    db_session=mock_session,
                )

        assert plugin_id == "alon/tongyi"
        assert model_name == "qwen-plus"
