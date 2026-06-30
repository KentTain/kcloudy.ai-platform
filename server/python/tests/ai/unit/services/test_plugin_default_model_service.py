"""PluginDefaultModelService 服务测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai.services.plugin_default_model_service import plugin_default_model_service
from ai.models.plugin_default_model import PluginDefaultModel


class TestPluginDefaultModelService:
    """服务测试类"""

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_get_default_model_found(self, mock_session):
        """测试获取默认模型（存在）"""
        mock_model = MagicMock(spec=PluginDefaultModel)
        mock_model.plugin_id = "alon/tongyi"
        mock_model.model_name = "qwen-plus"

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_model,
        ):
            result = await plugin_default_model_service.get_default_model(
                mock_session, "tenant-001", "llm"
            )

        assert result is not None
        assert result.plugin_id == "alon/tongyi"

    @pytest.mark.asyncio
    async def test_get_default_model_not_found(self, mock_session):
        """测试获取默认模型（不存在）"""
        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await plugin_default_model_service.get_default_model(
                mock_session, "tenant-001", "llm"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_set_default_model_create(self, mock_session):
        """测试设置默认模型（创建）"""
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
                await plugin_default_model_service.set_default_model(
                    mock_session,
                    tenant_id="tenant-001",
                    model_type="llm",
                    plugin_id="alon/tongyi",
                    model_name="qwen-plus",
                )
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_default_model_update(self, mock_session):
        """测试设置默认模型（更新）"""
        mock_existing = MagicMock(spec=PluginDefaultModel)
        mock_existing.model_name = "qwen-plus"

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_existing,
        ):
            await plugin_default_model_service.set_default_model(
                mock_session,
                tenant_id="tenant-001",
                model_type="llm",
                plugin_id="alon/tongyi",
                model_name="qwen-max",
            )
            assert mock_existing.model_name == "qwen-max"

    @pytest.mark.asyncio
    async def test_clear_default_model(self, mock_session):
        """测试清除默认模型"""
        mock_existing = MagicMock(spec=PluginDefaultModel)
        mock_existing.is_valid = True

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_existing,
        ):
            await plugin_default_model_service.clear_default_model(
                mock_session, "tenant-001", "llm"
            )
            assert mock_existing.is_valid is False
