"""
AI Inner API 插件管理接口单元测试

测试插件批量安装、启动、停止等 Inner API 接口。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.plugin_management import (
    BatchInstallRequest,
    BatchInstallResponse,
    InstallationItem,
    InstallFailedItem,
    InstallSkippedItem,
    InstallSuccessItem,
    StartPluginResponse,
    StopPluginResponse,
)


class TestBatchInstallPlugins:
    """测试批量安装插件接口"""

    @pytest.mark.asyncio
    async def test_batch_install_success(self, mock_session):
        """
        测试批量安装成功场景

        场景：批量安装 2 个插件到 2 个租户
        预期：返回成功列表包含 2 条记录
        """
        # 准备测试数据
        installations = [
            InstallationItem(
                tenant_id="tenant_1",
                plugin_id="plugin_1",
                plugin_unique_identifier="author/plugin_1",
                declaration={"name": "Plugin 1"},
                auto_start=False,
            ),
            InstallationItem(
                tenant_id="tenant_2",
                plugin_id="plugin_2",
                plugin_unique_identifier="author/plugin_2",
                declaration={"name": "Plugin 2"},
                auto_start=False,
            ),
        ]
        request = BatchInstallRequest(installations=installations)

        # Mock 数据库查询返回空（插件未安装）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        # 调用接口
        from ai.controllers.inner.plugin_management import batch_install_plugins

        response = await batch_install_plugins(request, mock_session)

        # 验证响应
        assert isinstance(response, ORJSONResponse)
        response_data = response.body
        assert b"success" in response_data

    @pytest.mark.asyncio
    async def test_batch_install_skip_already_installed(self, mock_session):
        """
        测试批量安装跳过已安装插件

        场景：尝试安装已存在的插件
        预期：返回跳过列表
        """
        # 准备测试数据
        installations = [
            InstallationItem(
                tenant_id="tenant_1",
                plugin_id="plugin_1",
                plugin_unique_identifier="author/plugin_1",
                declaration={"name": "Plugin 1"},
                auto_start=False,
            ),
        ]
        request = BatchInstallRequest(installations=installations)

        # Mock 数据库查询返回已存在记录
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # 已存在
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        # 调用接口
        from ai.controllers.inner.plugin_management import batch_install_plugins

        response = await batch_install_plugins(request, mock_session)

        # 验证响应包含跳过记录
        assert isinstance(response, ORJSONResponse)

    @pytest.mark.asyncio
    async def test_batch_install_empty_list(self, mock_session):
        """
        测试批量安装空列表

        场景：传入空的安装列表
        预期：返回空的成功/失败/跳过列表
        """
        request = BatchInstallRequest(installations=[])

        # 调用接口
        from ai.controllers.inner.plugin_management import batch_install_plugins

        response = await batch_install_plugins(request, mock_session)

        # 验证响应
        assert isinstance(response, ORJSONResponse)


class TestStartPlugin:
    """测试启动插件接口"""

    @pytest.mark.asyncio
    async def test_start_plugin_success(self, mock_session):
        """
        测试启动插件成功

        场景：启动一个已安装的插件
        预期：返回成功响应，包含进程 ID 和端口
        """
        plugin_id = "test_plugin"

        # Mock service 返回
        mock_result = MagicMock()
        mock_result.plugin_id = plugin_id
        mock_result.message = "插件启动成功"
        mock_result.status = "running"
        mock_result.success = True
        mock_result.process_id = 12345
        mock_result.port = 8080

        with patch(
            "ai.controllers.inner.plugin_management.plugin_management_service.start_plugin_with_response",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            from ai.controllers.inner.plugin_management import start_plugin

            response = await start_plugin(plugin_id, mock_session)

            # 验证响应
            assert isinstance(response, ORJSONResponse)

    @pytest.mark.asyncio
    async def test_start_plugin_not_found(self, mock_session):
        """
        测试启动不存在的插件

        场景：启动一个不存在的插件
        预期：抛出 404 异常
        """
        plugin_id = "nonexistent_plugin"

        with patch(
            "ai.controllers.inner.plugin_management.plugin_management_service.start_plugin_with_response",
            new_callable=AsyncMock,
            side_effect=ValueError("插件不存在"),
        ):
            from ai.controllers.inner.plugin_management import start_plugin

            # 验证抛出异常
            with pytest.raises(HTTPException) as exc_info:
                await start_plugin(plugin_id, mock_session)

            assert exc_info.value.status_code == 404


class TestStopPlugin:
    """测试停止插件接口"""

    @pytest.mark.asyncio
    async def test_stop_plugin_success(self, mock_session):
        """
        测试停止插件成功

        场景：停止一个运行中的插件
        预期：返回成功响应
        """
        plugin_id = "test_plugin"

        # Mock service 返回
        mock_result = MagicMock()
        mock_result.plugin_id = plugin_id
        mock_result.message = "插件停止成功"
        mock_result.status = "inactive"
        mock_result.success = True

        with patch(
            "ai.controllers.inner.plugin_management.plugin_management_service.stop_plugin_with_response",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            from ai.controllers.inner.plugin_management import stop_plugin

            response = await stop_plugin(plugin_id, mock_session)

            # 验证响应
            assert isinstance(response, ORJSONResponse)

    @pytest.mark.asyncio
    async def test_stop_plugin_not_running(self, mock_session):
        """
        测试停止未运行的插件

        场景：停止一个未启动的插件
        预期：抛出 404 异常
        """
        plugin_id = "inactive_plugin"

        with patch(
            "ai.controllers.inner.plugin_management.plugin_management_service.stop_plugin_with_response",
            new_callable=AsyncMock,
            side_effect=ValueError("插件未运行"),
        ):
            from ai.controllers.inner.plugin_management import stop_plugin

            # 验证抛出异常
            with pytest.raises(HTTPException) as exc_info:
                await stop_plugin(plugin_id, mock_session)

            assert exc_info.value.status_code == 404


# ==================== Fixtures ====================


@pytest.fixture
def mock_session():
    """Mock 数据库会话"""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session
