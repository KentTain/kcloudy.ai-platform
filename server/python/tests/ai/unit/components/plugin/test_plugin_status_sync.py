"""
插件启动/停止状态同步测试

测试 TenantPluginManager 的启动/停止方法：
- 配置检查
- 状态更新
- Tenant 通知
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class TestPluginStartStatusSync:
    """插件启动状态同步测试"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_start_plugin_checks_config_exists(self, mock_session):
        """测试启动插件时检查配置是否存在"""
        # 导入实际类
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        # 创建管理器实例
        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.plugins = {}  # 空插件列表
        manager.logger = MagicMock()

        # 调用实际方法
        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)

        # 执行测试并验证抛出错误
        with pytest.raises(ValueError, match="插件不存在"):
            await method("test-author/test-plugin", mock_session)

    @pytest.mark.asyncio
    async def test_start_plugin_updates_status_on_success(self, mock_session):
        """测试启动插件成功后更新状态"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        # 创建管理器实例
        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()

        # 模拟插件信息
        plugin_info = MagicMock()
        plugin_info.config = MagicMock()
        plugin_info.config.configuration = MagicMock()  # 配置完整
        manager.plugins = {"test-author/test-plugin": plugin_info}
        manager.running_plugins = {}

        # 模拟内部方法
        manager._start_plugin_internal = AsyncMock(return_value=True)
        manager._update_plugin_running_by_installation = AsyncMock()

        # 调用实际方法
        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)
        result = await method("test-author/test-plugin", mock_session)

        # 验证结果
        assert result is True
        manager._start_plugin_internal.assert_awaited_once_with(
            "test-author/test-plugin"
        )
        manager._update_plugin_running_by_installation.assert_awaited_once_with(
            mock_session, "test-author/test-plugin"
        )

    @pytest.mark.asyncio
    async def test_start_plugin_without_session_skips_update(self):
        """测试启动插件时没有 session 不更新状态"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        # 创建管理器实例
        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.logger = MagicMock()

        # 模拟插件信息
        plugin_info = MagicMock()
        plugin_info.config = MagicMock()
        plugin_info.config.configuration = MagicMock()
        manager.plugins = {"test-author/test-plugin": plugin_info}
        manager.running_plugins = {}

        # 模拟内部方法
        manager._start_plugin_internal = AsyncMock(return_value=True)
        manager._update_plugin_running_by_installation = AsyncMock()

        # 调用实际方法（不传 session）
        method = TenantPluginManager.start_plugin.__get__(manager, TenantPluginManager)
        result = await method("test-author/test-plugin", None)

        # 验证结果
        assert result is True
        manager._start_plugin_internal.assert_awaited_once()
        # 不应该调用更新方法
        manager._update_plugin_running_by_installation.assert_not_awaited()


class TestPluginStopStatusSync:
    """插件停止状态同步测试"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_runtime_state(self):
        """模拟运行时状态记录"""
        state = MagicMock()
        state.status = "active"
        state.last_started_at = datetime.now()
        state.last_stopped_at = None
        return state

    @pytest.mark.asyncio
    async def test_stop_plugin_not_running_returns_false(self, mock_session):
        """测试停止未运行的插件返回 False"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        # 创建管理器实例
        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.running_plugins = {}  # 没有运行中的插件
        manager.logger = MagicMock()

        # 调用实际方法
        method = TenantPluginManager.stop_plugin.__get__(manager, TenantPluginManager)
        result = await method("test-author/test-plugin", mock_session)

        # 验证结果
        assert result is False

    @pytest.mark.asyncio
    async def test_stop_plugin_updates_runtime_state(self, mock_session, mock_runtime_state):
        """测试停止插件时更新运行时状态"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        # 创建管理器实例
        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.running_plugins = {}
        manager.logger = MagicMock()
        manager._plugin_ready_cache = {}

        # 模拟运行中的插件
        runtime = MagicMock()
        runtime.stop = AsyncMock()
        manager.running_plugins["test-author/test-plugin"] = runtime

        # 模拟数据库查询返回运行时状态
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_runtime_state
        mock_session.execute.return_value = mock_result

        # 模拟 provider
        with patch(
            "ai.components.plugin.engine.core.plugin_manager.get_plugin_installation_provider"
        ) as mock_provider_func:
            mock_provider = MagicMock()
            mock_provider.update_installation = AsyncMock()
            mock_provider_func.return_value = mock_provider

            # 调用实际方法
            method = TenantPluginManager.stop_plugin.__get__(
                manager, TenantPluginManager
            )
            result = await method("test-author/test-plugin", mock_session)

            # 验证结果
            assert result is True
            runtime.stop.assert_awaited_once()

            # 验证更新了 runtime_state
            assert mock_runtime_state.status == "inactive"
            assert mock_runtime_state.last_stopped_at is not None

            # 验证通知了 tenant
            mock_provider.update_installation.assert_awaited_once_with(
                "test-tenant", "test-author/test-plugin", {"status": "INACTIVE"}
            )

    @pytest.mark.asyncio
    async def test_stop_plugin_without_session_skips_tenant_update(self):
        """测试停止插件时没有 session 不更新 tenant 状态"""
        from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager

        # 创建管理器实例
        manager = MagicMock(spec=TenantPluginManager)
        manager.tenant_id = "test-tenant"
        manager.running_plugins = {}
        manager.logger = MagicMock()
        manager._plugin_ready_cache = {}

        # 模拟运行中的插件
        runtime = MagicMock()
        runtime.stop = AsyncMock()
        manager.running_plugins["test-author/test-plugin"] = runtime

        # 调用实际方法（不传 session）
        method = TenantPluginManager.stop_plugin.__get__(
            manager, TenantPluginManager
        )
        result = await method("test-author/test-plugin", None)

        # 验证结果
        assert result is True
        runtime.stop.assert_awaited_once()
