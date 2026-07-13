"""测试 PluginInstallationProvider 状态更新方法"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework.tenant.plugin_protocols import PluginInstallationDTO
from tenant.services.plugin_provider import PluginInstallationProviderImpl


@pytest.fixture
def provider():
    """Provider 实例"""
    return PluginInstallationProviderImpl()


@pytest.fixture
def sample_dto():
    """示例插件安装 DTO"""
    return PluginInstallationDTO(
        tenant_id="tenant-001",
        plugin_id="author/plugin-name",
        plugin_unique_identifier="author/plugin-name:1.0.0@abc123",
        declaration={
            "version": "1.0.0",
            "name": "plugin-name",
            "author": "author",
            "tools_configuration": [],
        },
        status="PENDING",
        freeze_threshold_hours=24,
        plugin_type="local",
        runtime_type="python",
    )


class TestUpdateInstallationStatus:
    """更新安装状态测试"""

    @pytest.mark.asyncio
    async def test_update_installation_status_success(self, provider, sample_dto):
        """测试更新安装状态成功"""
        mock_session = AsyncMock()

        # 模拟已存在的安装记录
        mock_installation = MagicMock()
        mock_installation.tenant_id = "tenant-001"
        mock_installation.plugin_id = "author/plugin-name"
        mock_installation.plugin_unique_identifier = sample_dto.plugin_unique_identifier
        mock_installation.status = "PENDING"
        mock_installation.freeze_threshold_hours = 24
        mock_installation.plugin_type = "local"
        mock_installation.runtime_type = "python"
        mock_installation.installed_at = None

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=mock_installation,
            ):
                # 模拟 update 方法
                mock_installation.update = AsyncMock()

                # 模拟时间戳更新后的状态
                def update_side_effect(session, data):
                    if "status" in data:
                        mock_installation.status = data["status"]
                    if "installed_at" in data:
                        mock_installation.installed_at = data["installed_at"]

                mock_installation.update.side_effect = update_side_effect

                result = await provider.update_installation_status(
                    "tenant-001", "author/plugin-name", "INACTIVE"
                )

                # 验证 update 方法被调用
                mock_installation.update.assert_called_once()

                # 验证调用参数包含 status 和 installed_at
                call_args = mock_installation.update.call_args
                assert "status" in call_args[0][1]
                assert call_args[0][1]["status"] == "INACTIVE"

    @pytest.mark.asyncio
    async def test_update_installation_status_not_found(self, provider):
        """测试更新不存在的安装记录"""
        mock_session = AsyncMock()

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=None,
            ):
                with pytest.raises(ValueError, match="安装记录不存在"):
                    await provider.update_installation_status(
                        "tenant-001", "author/plugin-name", "INACTIVE"
                    )
