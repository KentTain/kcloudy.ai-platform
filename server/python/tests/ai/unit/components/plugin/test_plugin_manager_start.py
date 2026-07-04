"""
TenantPluginManager.start_plugin 方法单元测试

测试场景：
- 启动成功（完整配置）
- 启动失败（_start_plugin_internal 返回 False）
- 插件不存在
- 插件配置不存在
- 配置不完整时的警告
- 有 session 时更新运行时状态
- 无 session 时跳过状态更新
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class TestStartPluginSuccess:
    """启动插件成功场景"""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def manager(self):
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        mgr = MagicMock(spec=TenantPluginManager)
        mgr.tenant_id = "test-tenant"
        mgr.logger = MagicMock()

        plugin_info = MagicMock()
        plugin_info.config = MagicMock()
        plugin_info.config.configuration = MagicMock()
        mgr.plugins = {"test-author/test-plugin": plugin_info}
        mgr.running_plugins = {}

        mgr._start_plugin_internal = AsyncMock(return_value=True)
        mgr._update_plugin_running_by_installation = AsyncMock()

        return mgr

    @pytest.mark.asyncio
    async def test_start_success_returns_true(self, manager, mock_session):
        """启动成功返回 True"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)
        result = await method("test-author/test-plugin", mock_session)

        assert result is True

    @pytest.mark.asyncio
    async def test_start_success_calls_internal(self, manager, mock_session):
        """启动成功时调用 _start_plugin_internal"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)
        await method("test-author/test-plugin", mock_session)

        manager._start_plugin_internal.assert_awaited_once_with(
            "test-author/test-plugin"
        )

    @pytest.mark.asyncio
    async def test_start_success_updates_status(self, manager, mock_session):
        """启动成功且有 session 时更新运行时状态"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)
        await method("test-author/test-plugin", mock_session)

        manager._update_plugin_running_by_installation.assert_awaited_once_with(
            mock_session, "test-author/test-plugin"
        )

    @pytest.mark.asyncio
    async def test_start_success_without_session_skips_update(self, manager):
        """启动成功但无 session 时不更新状态"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)
        result = await method("test-author/test-plugin", None)

        assert result is True
        manager._update_plugin_running_by_installation.assert_not_awaited()


class TestStartPluginFailure:
    """启动插件失败场景"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_start_plugin_not_in_plugins_raises(self, mock_session):
        """插件不在 plugins 列表中时抛出 ValueError"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()
        manager.plugins = {}

        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)

        with pytest.raises(ValueError, match="插件不存在"):
            await method("nonexistent/plugin", mock_session)

    @pytest.mark.asyncio
    async def test_start_plugin_no_config_raises(self, mock_session):
        """插件配置为 None 时抛出 ValueError"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()

        plugin_info = MagicMock()
        plugin_info.config = None
        manager.plugins = {"test-author/test-plugin": plugin_info}

        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)

        with pytest.raises(ValueError, match="插件配置不存在"):
            await method("test-author/test-plugin", mock_session)

    @pytest.mark.asyncio
    async def test_start_plugin_internal_failure_returns_false(self, mock_session):
        """_start_plugin_internal 返回 False 时整体返回 False"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()

        plugin_info = MagicMock()
        plugin_info.config = MagicMock()
        plugin_info.config.configuration = MagicMock()
        manager.plugins = {"test-author/test-plugin": plugin_info}

        manager._start_plugin_internal = AsyncMock(return_value=False)
        manager._update_plugin_running_by_installation = AsyncMock()

        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)
        result = await method("test-author/test-plugin", mock_session)

        assert result is False
        manager._update_plugin_running_by_installation.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_start_plugin_incomplete_config_warns(self, mock_session):
        """配置不完整时记录警告但不阻止启动"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()

        plugin_info = MagicMock()
        plugin_info.config = MagicMock()
        # configuration 属性访问时抛出异常，模拟配置不完整
        type(plugin_info.config).configuration = property(
            lambda self: (_ for _ in ()).throw(ValueError("missing configuration"))
        )
        manager.plugins = {"test-author/test-plugin": plugin_info}

        manager._start_plugin_internal = AsyncMock(return_value=True)
        manager._update_plugin_running_by_installation = AsyncMock()

        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)
        result = await method("test-author/test-plugin", mock_session)

        # 不完整配置只警告不阻止，启动仍可继续
        assert result is True
        manager._start_plugin_internal.assert_awaited_once()
