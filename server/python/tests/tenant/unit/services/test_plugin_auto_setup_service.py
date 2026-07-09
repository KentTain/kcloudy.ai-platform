"""插件自动设置编排服务测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from framework.configs.plugin_auto_setup import (
    PluginAutoSetupConfig,
    PluginAutoSetupItem,
    VerificationConfig,
)
from framework.tenant.context import TenantContext
from tenant.services.plugin_auto_setup_service import (
    PluginAutoSetupService,
    StartupSetupResult,
)


@pytest.fixture
def mock_session():
    """模拟数据库会话"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture(autouse=True)
def tenant_context():
    """设置租户上下文"""
    TenantContext.set_tenant_id("test-tenant")
    yield
    TenantContext.clear()


@pytest.fixture
def auto_setup_config():
    """测试用自动设置配置"""
    return PluginAutoSetupConfig(
        enabled=True,
        plugins=[
            PluginAutoSetupItem(
                plugin_id="langgenius-tongyi",
                auto_install=True,
                auto_start=True,
                credentials={"api_key": "test-key"},
            )
        ],
        verification=VerificationConfig(enabled=False),
    )


@pytest.mark.asyncio
async def test_setup_plugins_disabled(mock_session):
    """测试自动设置已禁用"""
    service = PluginAutoSetupService()
    config = PluginAutoSetupConfig(enabled=False)

    result = await service.setup_plugins(mock_session, config)

    assert result.success_count == 0
    assert result.skipped_count == 0
    assert result.failed_count == 0


@pytest.mark.asyncio
async def test_setup_plugins_plugin_not_found(mock_session, auto_setup_config):
    """测试插件定义不存在"""
    service = PluginAutoSetupService()

    with patch(
        "tenant.services.plugin_auto_setup_service.TenantPluginInstallation.first_by_fields",
        new=AsyncMock(return_value=None),
    ), patch(
        "tenant.services.plugin_auto_setup_service.TenantPluginDefinition.one_by_field",
        new=AsyncMock(return_value=None),
    ):
        result = await service.setup_plugins(mock_session, auto_setup_config)

    assert result.failed_count == 1
    assert "插件定义不存在" in result.errors[0]


@pytest.mark.asyncio
async def test_setup_plugins_already_installed(mock_session, auto_setup_config):
    """测试插件已安装-跳过安装但仍执行配置和启动"""
    service = PluginAutoSetupService()
    mock_installation = MagicMock()
    mock_installation.plugin_id = "langgenius-tongyi"

    mock_config_provider = MagicMock()
    mock_config_provider.configure_plugin = AsyncMock()
    mock_installation_provider = MagicMock()
    mock_installation_provider.start_installation = AsyncMock()

    with patch(
        "tenant.services.plugin_auto_setup_service.TenantPluginInstallation.first_by_fields",
        new=AsyncMock(return_value=mock_installation),
    ), patch(
        "tenant.services.plugin_auto_setup_service.get_plugin_config_provider",
        return_value=mock_config_provider,
    ), patch(
        "tenant.services.plugin_auto_setup_service.get_plugin_installation_provider",
        return_value=mock_installation_provider,
    ):
        result = await service.setup_plugins(mock_session, auto_setup_config)

    assert result.skipped_count == 1
    assert result.success_count == 1
    mock_session.commit.assert_not_awaited()
    # 凭证配置和启动仍应执行（幂等更新）
    mock_config_provider.configure_plugin.assert_awaited_once_with(
        tenant_id="test-tenant",
        plugin_id="langgenius-tongyi",
        plugin_config={"api_key": "test-key"},
        runtime_config=None,
    )
    mock_installation_provider.start_installation.assert_awaited_once_with(
        "test-tenant", "langgenius-tongyi"
    )


@pytest.mark.asyncio
async def test_install_plugin_success(mock_session):
    """测试插件安装成功-返回 True"""
    service = PluginAutoSetupService()
    mock_definition = MagicMock()
    mock_definition.plugin_id = "langgenius-tongyi"
    mock_definition.plugin_unique_identifier = "langgenius-tongyi:0.2.0@abc123"
    mock_definition.install_type = "local"

    with patch(
        "tenant.services.plugin_auto_setup_service.TenantPluginInstallation.first_by_fields",
        new=AsyncMock(return_value=None),
    ), patch(
        "tenant.services.plugin_auto_setup_service.TenantPluginDefinition.one_by_field",
        new=AsyncMock(return_value=mock_definition),
    ):
        result = await service._install_plugin(
            mock_session,
            PluginAutoSetupItem(plugin_id="langgenius-tongyi"),
        )

    assert result is True
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_configure_credentials_delegates_to_provider():
    """测试配置凭证委托给 PluginConfigProvider"""
    service = PluginAutoSetupService()
    mock_provider = MagicMock()
    mock_provider.configure_plugin = AsyncMock()

    with patch(
        "tenant.services.plugin_auto_setup_service.get_plugin_config_provider",
        return_value=mock_provider,
    ):
        await service._configure_credentials("langgenius-tongyi", {"api_key": "test-key"})

    mock_provider.configure_plugin.assert_awaited_once_with(
        tenant_id="test-tenant",
        plugin_id="langgenius-tongyi",
        plugin_config={"api_key": "test-key"},
        runtime_config=None,
    )


@pytest.mark.asyncio
async def test_setup_plugins_full_success(mock_session, auto_setup_config):
    """测试完整成功流程：安装-提交-配置-启动"""
    service = PluginAutoSetupService()
    mock_definition = MagicMock()
    mock_definition.plugin_id = "langgenius-tongyi"
    mock_definition.plugin_unique_identifier = "langgenius-tongyi:0.2.0@abc123"
    mock_definition.install_type = "local"

    mock_config_provider = MagicMock()
    mock_config_provider.configure_plugin = AsyncMock()
    mock_installation_provider = MagicMock()
    mock_installation_provider.start_installation = AsyncMock()

    with patch(
        "tenant.services.plugin_auto_setup_service.TenantPluginInstallation.first_by_fields",
        new=AsyncMock(return_value=None),
    ), patch(
        "tenant.services.plugin_auto_setup_service.TenantPluginDefinition.one_by_field",
        new=AsyncMock(return_value=mock_definition),
    ), patch(
        "tenant.services.plugin_auto_setup_service.get_plugin_config_provider",
        return_value=mock_config_provider,
    ), patch(
        "tenant.services.plugin_auto_setup_service.get_plugin_installation_provider",
        return_value=mock_installation_provider,
    ):
        result = await service.setup_plugins(mock_session, auto_setup_config)

    assert result.success_count == 1
    assert result.failed_count == 0
    assert result.skipped_count == 0
    mock_session.commit.assert_awaited_once()
    mock_config_provider.configure_plugin.assert_awaited_once_with(
        tenant_id="test-tenant",
        plugin_id="langgenius-tongyi",
        plugin_config={"api_key": "test-key"},
        runtime_config=None,
    )
    mock_installation_provider.start_installation.assert_awaited_once_with(
        "test-tenant", "langgenius-tongyi"
    )
