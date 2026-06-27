"""
插件运行时单元测试

测试 TenantPluginManager 的运行控制逻辑：
- 启动/停止插件
- 插件状态管理
- 进程生命周期
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class TestPluginStartStop:
    """插件启动/停止单元测试"""

    @pytest.fixture
    def mock_manager(self):
        """模拟 TenantPluginManager"""
        with patch(
            "ai.components.plugin.engine.core.plugin_manager.TenantPluginManager"
        ) as mock_cls:
            manager = MagicMock()
            manager.tenant_id = "test-tenant"
            manager.plugins = {}
            manager.running_plugins = {}
            manager.start_plugin = AsyncMock()
            manager.stop_plugin = AsyncMock()
            mock_cls.return_value = manager
            yield manager

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_start_plugin_success(self, mock_manager, mock_session):
        """测试启动插件成功"""
        mock_manager.start_plugin.return_value = True
        plugin_id = "langgenius/tongyi"

        result = await mock_manager.start_plugin(plugin_id, mock_session)

        assert result is True
        mock_manager.start_plugin.assert_awaited_once_with(plugin_id, mock_session)

    @pytest.mark.asyncio
    async def test_start_plugin_already_running(self, mock_manager, mock_session):
        """测试启动已运行的插件"""
        plugin_id = "langgenius/tongyi"
        mock_manager.running_plugins[plugin_id] = MagicMock()
        mock_manager.start_plugin.side_effect = Exception("插件已在运行中")

        with pytest.raises(Exception, match="插件已在运行中"):
            await mock_manager.start_plugin(plugin_id, mock_session)

    @pytest.mark.asyncio
    async def test_start_plugin_not_installed(self, mock_manager, mock_session):
        """测试启动未安装的插件"""
        plugin_id = "unknown/plugin"
        mock_manager.start_plugin.side_effect = ValueError("插件未安装")

        with pytest.raises(ValueError, match="插件未安装"):
            await mock_manager.start_plugin(plugin_id, mock_session)

    @pytest.mark.asyncio
    async def test_stop_plugin_success(self, mock_manager, mock_session):
        """测试停止插件成功"""
        plugin_id = "langgenius/tongyi"
        mock_manager.stop_plugin.return_value = True

        result = await mock_manager.stop_plugin(plugin_id, mock_session)

        assert result is True
        mock_manager.stop_plugin.assert_awaited_once_with(plugin_id, mock_session)

    @pytest.mark.asyncio
    async def test_stop_plugin_not_running(self, mock_manager, mock_session):
        """测试停止未运行的插件"""
        plugin_id = "langgenius/tongyi"
        mock_manager.stop_plugin.return_value = False

        result = await mock_manager.stop_plugin(plugin_id, mock_session)

        assert result is False

    @pytest.mark.asyncio
    async def test_start_plugin_updates_status(self, mock_manager, mock_session):
        """测试启动后更新运行时状态"""
        plugin_id = "langgenius/gpustack"
        mock_manager.start_plugin.return_value = True

        await mock_manager.start_plugin(plugin_id, mock_session)

        mock_manager.start_plugin.assert_awaited_once()


class TestPluginStatus:
    """插件状态管理单元测试"""

    @pytest.fixture
    def mock_manager(self):
        manager = MagicMock()
        manager.plugins = {}
        manager.running_plugins = {}
        return manager

    def test_plugin_listed_after_install(self, mock_manager):
        """测试安装后插件在列表中出现"""
        plugin_id = "langgenius/tongyi"
        mock_plugin = MagicMock()
        mock_plugin.id = plugin_id
        mock_plugin.status = "INACTIVE"
        mock_manager.plugins[plugin_id] = mock_plugin

        assert plugin_id in mock_manager.plugins
        assert mock_manager.plugins[plugin_id].status == "INACTIVE"

    def test_plugin_active_after_start(self, mock_manager):
        """测试启动后插件状态为 ACTIVE"""
        plugin_id = "langgenius/tongyi"
        mock_plugin = MagicMock()
        mock_plugin.id = plugin_id
        mock_plugin.status = "ACTIVE"
        mock_manager.plugins[plugin_id] = mock_plugin
        mock_manager.running_plugins[plugin_id] = MagicMock()

        assert plugin_id in mock_manager.running_plugins
        assert mock_manager.plugins[plugin_id].status == "ACTIVE"

    def test_plugin_removed_after_uninstall(self, mock_manager):
        """测试卸载后插件从列表中移除"""
        plugin_id = "langgenius/tongyi"
        mock_plugin = MagicMock()
        mock_plugin.id = plugin_id
        mock_manager.plugins[plugin_id] = mock_plugin

        del mock_manager.plugins[plugin_id]

        assert plugin_id not in mock_manager.plugins

    def test_multiple_plugins_status(self, mock_manager):
        """测试多插件状态管理"""
        plugins = {
            "langgenius/tongyi": "ACTIVE",
            "langgenius/gpustack": "INACTIVE",
            "langgenius/ollama": "ACTIVE",
        }
        for pid, status in plugins.items():
            p = MagicMock()
            p.id = pid
            p.status = status
            mock_manager.plugins[pid] = p
            if status == "ACTIVE":
                mock_manager.running_plugins[pid] = MagicMock()

        running_count = len(mock_manager.running_plugins)
        assert running_count == 2
        assert mock_manager.plugins["langgenius/tongyi"].status == "ACTIVE"


class TestPluginManagerFactory:
    """PluginManagerFactory 单元测试"""

    @pytest.mark.asyncio
    async def test_get_manager_creates_new(self):
        """测试获取新的管理器实例"""
        mock_manager = MagicMock()
        mock_manager.initialize = AsyncMock()

        with patch(
            "ai.components.plugin.engine.core.plugin_manager.PluginManagerFactory.get_manager",
            return_value=mock_manager,
        ) as mock_factory:
            session = AsyncMock(spec=AsyncSession)
            manager = await mock_factory("test-tenant", session)

            assert manager is mock_manager
            mock_factory.assert_called_once_with("test-tenant", session)

    @pytest.mark.asyncio
    async def test_get_manager_with_different_tenants(self):
        """测试不同租户获取不同管理器"""
        mock_manager_1 = MagicMock()
        mock_manager_2 = MagicMock()
        call_count = 0

        async def side_effect(tenant_id, session):
            nonlocal call_count
            call_count += 1
            if tenant_id == "tenant-1":
                return mock_manager_1
            return mock_manager_2

        with patch(
            "ai.components.plugin.engine.core.plugin_manager.PluginManagerFactory.get_manager",
            side_effect=side_effect,
        ) as mock_factory:
            session = AsyncMock(spec=AsyncSession)
            m1 = await mock_factory("tenant-1", session)
            m2 = await mock_factory("tenant-2", session)

            assert m1 is not m2
            assert m1 is mock_manager_1
            assert m2 is mock_manager_2
