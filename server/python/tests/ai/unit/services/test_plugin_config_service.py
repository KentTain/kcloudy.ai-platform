"""测试 PluginConfigService

测试插件配置、测试连接、启动、停止功能。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai.services.plugin import PluginConfigService
from ai.schemas.plugin_config import (
    PluginConfigResponse,
    PluginTestResponse,
    PluginStartResponse,
    PluginStopResponse,
)


@pytest.fixture
def mock_session():
    """模拟数据库会话"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_plugin_config():
    """模拟插件配置"""
    config = MagicMock()
    config.plugin_id = "test/plugin"
    config.plugin_config = {"api_key": "test_key", "validated": None}
    config.runtime_config = {"timeout": 30}
    return config


@pytest.fixture
def mock_installation():
    """模拟安装记录"""
    installation = MagicMock()
    installation.plugin_id = "test/plugin"
    installation.plugin_unique_identifier = "test/plugin:1.0.0@abc123"
    return installation


class TestPluginConfigService:
    """PluginConfigService 测试类"""

    @pytest.mark.asyncio
    async def test_config_plugin_creates_new_config(
        self, mock_session, mock_installation
    ):
        """测试配置插件时创建新配置记录"""
        service = PluginConfigService()

        # 模拟查询返回 None（不存在配置）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # 模拟 provider 返回安装记录
        with patch(
            "framework.tenant.plugin_protocols.get_plugin_installation_provider"
        ) as mock_provider:
            mock_provider_instance = MagicMock()
            mock_provider_instance.get_installation = AsyncMock(
                return_value=mock_installation
            )
            mock_provider.return_value = mock_provider_instance

            result = await service.config_plugin(
                session=mock_session,
                tenant_id="test_tenant",
                plugin_id="test/plugin",
                plugin_config={"api_key": "test_key"},
                runtime_config={"timeout": 30},
            )

        # 验证结果
        assert isinstance(result, PluginConfigResponse)
        assert result.plugin_id == "test/plugin"
        assert result.validated is None

        # 验证调用了 session.add
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_config_plugin_updates_existing_config(
        self, mock_session, mock_plugin_config
    ):
        """测试配置插件时更新现有配置"""
        service = PluginConfigService()

        # 模拟查询返回现有配置
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_plugin_config
        mock_session.execute.return_value = mock_result

        result = await service.config_plugin(
            session=mock_session,
            tenant_id="test_tenant",
            plugin_id="test/plugin",
            plugin_config={"api_key": "new_key"},
            runtime_config={"timeout": 60},
        )

        # 验证结果
        assert isinstance(result, PluginConfigResponse)
        assert result.plugin_id == "test/plugin"

        # 验证配置已更新
        assert mock_plugin_config.plugin_config == {"api_key": "new_key", "validated": None}
        assert mock_plugin_config.runtime_config == {"timeout": 60}

    @pytest.mark.asyncio
    async def test_test_plugin_without_config(self, mock_session):
        """测试未配置的插件测试连接"""
        service = PluginConfigService()

        # 模拟查询返回 None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.test_plugin(
            session=mock_session,
            tenant_id="test_tenant",
            plugin_id="test/plugin",
        )

        # 验证结果
        assert isinstance(result, PluginTestResponse)
        assert result.plugin_id == "test/plugin"
        assert result.validated is False
        assert "未配置" in result.message

    @pytest.mark.asyncio
    async def test_test_plugin_success(self, mock_session, mock_plugin_config):
        """测试插件连接成功"""
        service = PluginConfigService()

        # 模拟查询返回配置
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_plugin_config
        mock_session.execute.return_value = mock_result

        # Mock PluginManagerFactory 避免依赖 PluginInstallationProvider
        with patch(
            "ai.components.plugin.engine.core.plugin_manager.PluginManagerFactory"
        ) as mock_factory:
            mock_manager = MagicMock()
            mock_manager.test_plugin_connection = AsyncMock(
                return_value=(True, "连接成功")
            )
            mock_factory.get_manager = AsyncMock(return_value=mock_manager)

            result = await service.test_plugin(
                session=mock_session,
                tenant_id="test_tenant",
                plugin_id="test/plugin",
            )

        # 验证结果
        assert isinstance(result, PluginTestResponse)
        assert result.plugin_id == "test/plugin"
        assert result.validated is True
        assert result.message == "连接成功"

        # 验证验证状态已更新
        assert mock_plugin_config.plugin_config["validated"] is True

    @pytest.mark.asyncio
    async def test_start_plugin_with_warning(self, mock_session):
        """测试启动插件时给出警告（未配置）"""
        service = PluginConfigService()

        # 模拟查询返回 None（未配置）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # 模拟 plugin_management_service
        with patch(
            "ai.services.plugin_config_service.plugin_management_service"
        ) as mock_mgmt:
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.status = "running"
            mock_response.port = 50001
            mock_mgmt.start_plugin_with_response = AsyncMock(return_value=mock_response)

            result = await service.start_plugin(
                session=mock_session,
                tenant_id="test_tenant",
                plugin_id="test/plugin",
            )

        # 验证结果
        assert isinstance(result, PluginStartResponse)
        assert result.plugin_id == "test/plugin"
        assert result.status == "ACTIVE"
        assert result.port == 50001
        assert "未配置" in result.warning

    @pytest.mark.asyncio
    async def test_start_plugin_success(self, mock_session, mock_plugin_config):
        """测试启动插件成功"""
        service = PluginConfigService()

        # 模拟查询返回配置
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_plugin_config
        mock_session.execute.return_value = mock_result

        # 模拟 plugin_management_service
        with patch(
            "ai.services.plugin_config_service.plugin_management_service"
        ) as mock_mgmt:
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.status = "running"
            mock_response.port = 50001
            mock_mgmt.start_plugin_with_response = AsyncMock(return_value=mock_response)

            result = await service.start_plugin(
                session=mock_session,
                tenant_id="test_tenant",
                plugin_id="test/plugin",
            )

        # 验证结果
        assert isinstance(result, PluginStartResponse)
        assert result.plugin_id == "test/plugin"
        assert result.status == "ACTIVE"
        assert result.port == 50001

    @pytest.mark.asyncio
    async def test_stop_plugin_success(self, mock_session):
        """测试停止插件成功"""
        service = PluginConfigService()

        # 模拟 plugin_management_service
        with patch(
            "ai.services.plugin_config_service.plugin_management_service"
        ) as mock_mgmt:
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.status = "inactive"
            mock_mgmt.stop_plugin_with_response = AsyncMock(return_value=mock_response)

            result = await service.stop_plugin(
                session=mock_session,
                tenant_id="test_tenant",
                plugin_id="test/plugin",
            )

        # 验证结果
        assert isinstance(result, PluginStopResponse)
        assert result.plugin_id == "test/plugin"
        assert result.status == "INACTIVE"

    @pytest.mark.asyncio
    async def test_stop_plugin_not_running(self, mock_session):
        """测试停止未运行的插件"""
        service = PluginConfigService()

        # 模拟 plugin_management_service
        with patch(
            "ai.services.plugin_config_service.plugin_management_service"
        ) as mock_mgmt:
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.status = "inactive"
            mock_mgmt.stop_plugin_with_response = AsyncMock(return_value=mock_response)

            result = await service.stop_plugin(
                session=mock_session,
                tenant_id="test_tenant",
                plugin_id="test/plugin",
            )

        # 验证结果
        assert isinstance(result, PluginStopResponse)
        assert result.plugin_id == "test/plugin"
        assert result.status == "INACTIVE"
