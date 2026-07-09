"""测试 PluginConfigProviderImpl

测试 AI 模块对 PluginConfigProvider 协议的实现：
- 委托给 plugin_config_service.config_plugin
- 使用独立的 Session 管理事务
- 返回 PluginConfigDTO
"""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.plugin_config import PluginConfigResponse
from framework.tenant.plugin_protocols import PluginConfigDTO


@pytest.fixture
def mock_session():
    """模拟数据库会话"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_task_session_cm(mock_session):
    """模拟 get_task_session 返回的异步上下文管理器

    get_task_session() 返回一个异步上下文管理器，
    `async with get_task_session() as session:` 会通过 __aenter__ 拿到 session。
    """
    cm = AsyncMock()
    cm.__aenter__.return_value = mock_session
    cm.__aexit__.return_value = None
    return cm


class TestPluginConfigProviderImpl:
    """PluginConfigProviderImpl 测试类"""

    @pytest.mark.asyncio
    async def test_configure_plugin_delegates_to_config_service(
        self, mock_session, mock_task_session_cm
    ):
        """测试 configure_plugin 委托给 plugin_config_service.config_plugin"""
        from ai.services.plugin_config_provider import plugin_config_provider_impl

        # 模拟 config_plugin 返回 PluginConfigResponse
        mock_response = PluginConfigResponse(plugin_id="test/plugin", validated=True)

        with patch(
            "ai.services.plugin_config_provider.plugin_config_service"
        ) as mock_service, patch(
            "ai.services.plugin_config_provider.get_task_session",
            return_value=mock_task_session_cm,
        ):
            mock_service.config_plugin = AsyncMock(return_value=mock_response)

            result = await plugin_config_provider_impl.configure_plugin(
                tenant_id="test_tenant",
                plugin_id="test/plugin",
                plugin_config={"api_key": "test_key"},
                runtime_config={"timeout": 30},
            )

        # 验证委托调用了 config_plugin，且传入独立创建的 session
        mock_service.config_plugin.assert_awaited_once_with(
            session=mock_session,
            tenant_id="test_tenant",
            plugin_id="test/plugin",
            plugin_config={"api_key": "test_key"},
            runtime_config={"timeout": 30},
        )

        # 验证返回值为 PluginConfigDTO 且 plugin_id 正确
        assert isinstance(result, PluginConfigDTO)
        assert result.plugin_id == "test/plugin"

    @pytest.mark.asyncio
    async def test_configure_plugin_returns_dto_with_configs(
        self, mock_session, mock_task_session_cm
    ):
        """测试返回的 DTO 携带传入的 plugin_config / runtime_config"""
        from ai.services.plugin_config_provider import plugin_config_provider_impl

        mock_response = PluginConfigResponse(plugin_id="test/plugin", validated=True)

        with patch(
            "ai.services.plugin_config_provider.plugin_config_service"
        ) as mock_service, patch(
            "ai.services.plugin_config_provider.get_task_session",
            return_value=mock_task_session_cm,
        ):
            mock_service.config_plugin = AsyncMock(return_value=mock_response)

            result = await plugin_config_provider_impl.configure_plugin(
                tenant_id="test_tenant",
                plugin_id="test/plugin",
                plugin_config={"api_key": "test_key", "endpoint": "http://x"},
                runtime_config={"timeout": 60, "retries": 3},
            )

        assert isinstance(result, PluginConfigDTO)
        assert result.plugin_config == {"api_key": "test_key", "endpoint": "http://x"}
        assert result.runtime_config == {"timeout": 60, "retries": 3}

    @pytest.mark.asyncio
    async def test_configure_plugin_null_configs(self, mock_session, mock_task_session_cm):
        """测试传入 None 配置时不报错且 DTO 字段为 None"""
        from ai.services.plugin_config_provider import plugin_config_provider_impl

        mock_response = PluginConfigResponse(plugin_id="test/plugin", validated=None)

        with patch(
            "ai.services.plugin_config_provider.plugin_config_service"
        ) as mock_service, patch(
            "ai.services.plugin_config_provider.get_task_session",
            return_value=mock_task_session_cm,
        ):
            mock_service.config_plugin = AsyncMock(return_value=mock_response)

            result = await plugin_config_provider_impl.configure_plugin(
                tenant_id="test_tenant",
                plugin_id="test/plugin",
                plugin_config=None,
                runtime_config=None,
            )

        assert isinstance(result, PluginConfigDTO)
        assert result.plugin_id == "test/plugin"
        assert result.plugin_config is None
        assert result.runtime_config is None
