"""
TenantPluginManager.stop_plugin 方法单元测试

测试场景：
- 停止运行中的插件成功
- 停止未运行的插件返回 False
- 有 session 时更新 runtime_state 和通知 tenant
- 无 session 时跳过状态更新
- 清除插件准备状态缓存
- 运行时 stop() 抛异常时返回 False
- tenant 状态更新失败不影响停止结果
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class TestStopPluginSuccess:
    """停止插件成功场景"""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_runtime_state(self):
        state = MagicMock()
        state.status = "active"
        state.last_started_at = datetime.now()
        state.last_stopped_at = None
        return state

    @pytest.fixture
    def manager_with_running_plugin(self, mock_session):
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        mgr = MagicMock(spec=TenantPluginManager)
        mgr.tenant_id = "test-tenant"
        mgr.logger = MagicMock()
        mgr._plugin_ready_cache = {"test-author/test-plugin": 1000.0}

        runtime = MagicMock()
        runtime.stop = AsyncMock()
        mgr.running_plugins = {"test-author/test-plugin": runtime}

        return mgr

    @pytest.mark.asyncio
    async def test_stop_success_returns_true(
        self, manager_with_running_plugin, mock_session
    ):
        """停止成功返回 True"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        method = TenantPluginManager.stop_plugin.__get__(
            manager_with_running_plugin, TenantPluginManager
        )

        with patch(
            "ai.components.plugin.engine.core.plugin_manager.get_plugin_installation_provider"
        ) as mock_provider_func:
            mock_provider_func.return_value = MagicMock(
                update_installation=AsyncMock()
            )
            result = await method("test-author/test-plugin", mock_session)

        assert result is True

    @pytest.mark.asyncio
    async def test_stop_success_removes_from_running_plugins(
        self, manager_with_running_plugin, mock_session
    ):
        """停止成功后从 running_plugins 中移除"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        method = TenantPluginManager.stop_plugin.__get__(
            manager_with_running_plugin, TenantPluginManager
        )

        with patch(
            "ai.components.plugin.engine.core.plugin_manager.get_plugin_installation_provider"
        ) as mock_provider_func:
            mock_provider_func.return_value = MagicMock(
                update_installation=AsyncMock()
            )
            await method("test-author/test-plugin", mock_session)

        assert "test-author/test-plugin" not in manager_with_running_plugin.running_plugins

    @pytest.mark.asyncio
    async def test_stop_success_calls_runtime_stop(
        self, manager_with_running_plugin, mock_session
    ):
        """停止成功时调用 runtime.stop()"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        runtime = manager_with_running_plugin.running_plugins["test-author/test-plugin"]
        method = TenantPluginManager.stop_plugin.__get__(
            manager_with_running_plugin, TenantPluginManager
        )

        with patch(
            "ai.components.plugin.engine.core.plugin_manager.get_plugin_installation_provider"
        ) as mock_provider_func:
            mock_provider_func.return_value = MagicMock(
                update_installation=AsyncMock()
            )
            await method("test-author/test-plugin", mock_session)

        runtime.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_success_clears_ready_cache(
        self, manager_with_running_plugin, mock_session
    ):
        """停止成功后清除准备状态缓存"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        method = TenantPluginManager.stop_plugin.__get__(
            manager_with_running_plugin, TenantPluginManager
        )

        with patch(
            "ai.components.plugin.engine.core.plugin_manager.get_plugin_installation_provider"
        ) as mock_provider_func:
            mock_provider_func.return_value = MagicMock(
                update_installation=AsyncMock()
            )
            await method("test-author/test-plugin", mock_session)

        assert "test-author/test-plugin" not in manager_with_running_plugin._plugin_ready_cache


class TestStopPluginNotRunning:
    """停止未运行插件场景"""

    @pytest.mark.asyncio
    async def test_stop_not_running_returns_false(self):
        """停止未运行的插件返回 False"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.running_plugins = {}
        manager.logger = MagicMock()

        method = TenantPluginManager.stop_plugin.__get__(manager, TenantPluginManager)
        result = await method("test-author/test-plugin", AsyncMock(spec=AsyncSession))

        assert result is False


class TestStopPluginWithSession:
    """停止插件时 session 相关场景"""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_runtime_state(self):
        state = MagicMock()
        state.status = "active"
        state.last_stopped_at = None
        return state

    @pytest.mark.asyncio
    async def test_stop_updates_runtime_state_to_inactive(
        self, mock_session, mock_runtime_state
    ):
        """有 session 时更新 runtime_state 为 inactive"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()
        manager._plugin_ready_cache = {}

        runtime = MagicMock()
        runtime.stop = AsyncMock()
        manager.running_plugins = {"test-author/test-plugin": runtime}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_runtime_state
        mock_session.execute.return_value = mock_result

        with patch(
            "ai.components.plugin.engine.core.plugin_manager.get_plugin_installation_provider"
        ) as mock_provider_func:
            mock_provider_func.return_value = MagicMock(
                update_installation=AsyncMock()
            )
            method = TenantPluginManager.stop_plugin.__get__(
                manager, TenantPluginManager
            )
            await method("test-author/test-plugin", mock_session)

        assert mock_runtime_state.status == "inactive"
        assert mock_runtime_state.last_stopped_at is not None
        mock_session.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_stop_notifies_tenant_status_inactive(
        self, mock_session, mock_runtime_state
    ):
        """有 session 时通知 tenant 更新状态为 INACTIVE"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()
        manager._plugin_ready_cache = {}

        runtime = MagicMock()
        runtime.stop = AsyncMock()
        manager.running_plugins = {"test-author/test-plugin": runtime}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_runtime_state
        mock_session.execute.return_value = mock_result

        with patch(
            "ai.components.plugin.engine.core.plugin_manager.get_plugin_installation_provider"
        ) as mock_provider_func:
            mock_provider = MagicMock()
            mock_provider.update_installation = AsyncMock()
            mock_provider_func.return_value = mock_provider

            method = TenantPluginManager.stop_plugin.__get__(
                manager, TenantPluginManager
            )
            await method("test-author/test-plugin", mock_session)

            mock_provider.update_installation.assert_awaited_once_with(
                "test-tenant",
                "test-author/test-plugin",
                {"status": "INACTIVE"},
            )

    @pytest.mark.asyncio
    async def test_stop_without_session_skips_all_updates(self):
        """无 session 时不更新 runtime_state 也不通知 tenant"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()
        manager._plugin_ready_cache = {}

        runtime = MagicMock()
        runtime.stop = AsyncMock()
        manager.running_plugins = {"test-author/test-plugin": runtime}

        method = TenantPluginManager.stop_plugin.__get__(
            manager, TenantPluginManager
        )
        result = await method("test-author/test-plugin", None)

        assert result is True
        runtime.stop.assert_awaited_once()


class TestStopPluginErrorHandling:
    """停止插件异常处理场景"""

    @pytest.mark.asyncio
    async def test_stop_runtime_exception_returns_false(self):
        """runtime.stop() 抛异常时返回 False"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()
        manager._plugin_ready_cache = {}

        runtime = MagicMock()
        runtime.stop = AsyncMock(side_effect=RuntimeError("进程已退出"))
        manager.running_plugins = {"test-author/test-plugin": runtime}

        method = TenantPluginManager.stop_plugin.__get__(
            manager, TenantPluginManager
        )
        result = await method("test-author/test-plugin", None)

        assert result is False

    @pytest.mark.asyncio
    async def test_stop_tenant_update_failure_does_not_affect_result(self):
        """tenant 状态更新失败不影响停止结果"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()
        manager._plugin_ready_cache = {}

        runtime = MagicMock()
        runtime.stop = AsyncMock()
        manager.running_plugins = {"test-author/test-plugin": runtime}

        with patch(
            "ai.components.plugin.engine.core.plugin_manager.get_plugin_installation_provider"
        ) as mock_provider_func:
            mock_provider = MagicMock()
            mock_provider.update_installation = AsyncMock(
                side_effect=Exception("tenant 不可达")
            )
            mock_provider_func.return_value = mock_provider

            method = TenantPluginManager.stop_plugin.__get__(
                manager, TenantPluginManager
            )
            result = await method("test-author/test-plugin", mock_session)

        # 即使 tenant 更新失败，插件仍然停止成功
        assert result is True

    @pytest.mark.asyncio
    async def test_stop_runtime_state_not_found_still_succeeds(self):
        """runtime_state 记录不存在时仍能停止成功"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # 无运行时状态记录
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()

        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()
        manager._plugin_ready_cache = {}

        runtime = MagicMock()
        runtime.stop = AsyncMock()
        manager.running_plugins = {"test-author/test-plugin": runtime}

        with patch(
            "ai.components.plugin.engine.core.plugin_manager.get_plugin_installation_provider"
        ) as mock_provider_func:
            mock_provider_func.return_value = MagicMock(
                update_installation=AsyncMock()
            )
            method = TenantPluginManager.stop_plugin.__get__(
                manager, TenantPluginManager
            )
            result = await method("test-author/test-plugin", mock_session)

        assert result is True
