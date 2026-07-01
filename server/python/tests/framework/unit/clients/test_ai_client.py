"""
AI 客户端单元测试

测试 AIClient 的双模式调用能力（单体模式 / 微服务模式）。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.plugin_management import (
    BatchInstallResponse,
    InstallationItem,
    StartPluginResponse,
    StopPluginResponse,
)
from framework.clients.ai_client import AIClient, get_ai_client


class TestAIClientMonolithicMode:
    """测试 AI 客户端单体模式（直接 Service 调用）"""

    @pytest.mark.asyncio
    async def test_start_plugin_monolithic_mode(self, mock_session):
        """
        测试单体模式启动插件

        场景：单体模式调用 start_plugin
        预期：直接调用 plugin_management_service，返回响应
        """
        # 准备测试数据
        tenant_id = "test_tenant"
        plugin_id = "test_plugin"

        # Mock service 返回
        mock_service_result = MagicMock()
        mock_service_result.plugin_id = plugin_id
        mock_service_result.message = "插件启动成功"
        mock_service_result.status = "running"
        mock_service_result.success = True
        mock_service_result.process_id = 12345
        mock_service_result.port = 8080

        with patch(
            "ai.services.plugin.plugin_management_service.start_plugin_with_response",
            new_callable=AsyncMock,
            return_value=mock_service_result,
        ):
            # 创建客户端（单体模式，不传 inner_url）
            client = AIClient()
            result = await client.start_plugin(mock_session, tenant_id, plugin_id)

            # 验证结果
            assert isinstance(result, StartPluginResponse)
            assert result.plugin_id == plugin_id
            assert result.success is True
            assert result.process_id == 12345
            assert result.port == 8080

    @pytest.mark.asyncio
    async def test_stop_plugin_monolithic_mode(self, mock_session):
        """
        测试单体模式停止插件

        场景：单体模式调用 stop_plugin
        预期：直接调用 plugin_management_service，返回响应
        """
        tenant_id = "test_tenant"
        plugin_id = "test_plugin"

        # Mock service 返回
        mock_service_result = MagicMock()
        mock_service_result.plugin_id = plugin_id
        mock_service_result.message = "插件停止成功"
        mock_service_result.status = "inactive"
        mock_service_result.success = True

        with patch(
            "ai.services.plugin.plugin_management_service.stop_plugin_with_response",
            new_callable=AsyncMock,
            return_value=mock_service_result,
        ):
            client = AIClient()
            result = await client.stop_plugin(mock_session, tenant_id, plugin_id)

            assert isinstance(result, StopPluginResponse)
            assert result.plugin_id == plugin_id
            assert result.success is True

    @pytest.mark.asyncio
    async def test_batch_install_plugins_monolithic_mode(self, mock_session):
        """
        测试单体模式批量安装插件

        场景：单体模式调用 batch_install_plugins
        预期：直接操作数据库创建 PluginConfig 和 PluginRuntimeState
        """
        installations = [
            InstallationItem(
                tenant_id="tenant_1",
                plugin_id="plugin_1",
                plugin_unique_identifier="author/plugin_1",
                declaration={"name": "Plugin 1"},
                auto_start=False,
            ),
        ]

        # Mock 数据库查询返回空
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        client = AIClient()
        result = await client.batch_install_plugins(mock_session, installations)

        assert isinstance(result, BatchInstallResponse)
        assert len(result.success) == 1
        assert result.success[0].tenant_id == "tenant_1"
        assert result.success[0].plugin_id == "plugin_1"

    @pytest.mark.asyncio
    async def test_batch_install_empty_list(self, mock_session):
        """
        测试批量安装空列表

        场景：传入空的安装列表
        预期：返回空列表响应
        """
        client = AIClient()
        result = await client.batch_install_plugins(mock_session, [])

        assert isinstance(result, BatchInstallResponse)
        assert len(result.success) == 0
        assert len(result.failed) == 0
        assert len(result.skipped) == 0


class TestAIClientMicroserviceMode:
    """测试 AI 客户端微服务模式（HTTP 调用）"""

    @pytest.mark.asyncio
    async def test_start_plugin_microservice_mode(self, mock_session):
        """
        测试微服务模式启动插件

        场景：微服务模式调用 start_plugin
        预期：通过 HTTP 调用 Inner API
        """
        tenant_id = "test_tenant"
        plugin_id = "test_plugin"

        # Mock HTTP 客户端返回
        mock_http_response = StartPluginResponse(
            plugin_id=plugin_id,
            message="插件启动成功",
            status="running",
            success=True,
            process_id=12345,
            port=8080,
        )

        with patch(
            "framework.clients.inner_http_client.InnerHttpClient.post",
            new_callable=AsyncMock,
            return_value=mock_http_response,
        ):
            # 创建客户端（微服务模式，传入 inner_url）
            client = AIClient(inner_url="http://ai-service:8000")
            result = await client.start_plugin(mock_session, tenant_id, plugin_id)

            assert isinstance(result, StartPluginResponse)
            assert result.plugin_id == plugin_id
            assert result.success is True

    @pytest.mark.asyncio
    async def test_stop_plugin_microservice_mode(self, mock_session):
        """
        测试微服务模式停止插件

        场景：微服务模式调用 stop_plugin
        预期：通过 HTTP 调用 Inner API
        """
        tenant_id = "test_tenant"
        plugin_id = "test_plugin"

        mock_http_response = StopPluginResponse(
            plugin_id=plugin_id,
            message="插件停止成功",
            status="inactive",
            success=True,
        )

        with patch(
            "framework.clients.inner_http_client.InnerHttpClient.post",
            new_callable=AsyncMock,
            return_value=mock_http_response,
        ):
            client = AIClient(inner_url="http://ai-service:8000")
            result = await client.stop_plugin(mock_session, tenant_id, plugin_id)

            assert isinstance(result, StopPluginResponse)
            assert result.plugin_id == plugin_id
            assert result.success is True

    @pytest.mark.asyncio
    async def test_batch_install_plugins_microservice_mode(self, mock_session):
        """
        测试微服务模式批量安装插件

        场景：微服务模式调用 batch_install_plugins
        预期：通过 HTTP 调用 Inner API
        """
        installations = [
            InstallationItem(
                tenant_id="tenant_1",
                plugin_id="plugin_1",
                plugin_unique_identifier="author/plugin_1",
                declaration={"name": "Plugin 1"},
                auto_start=False,
            ),
        ]

        mock_http_response = BatchInstallResponse(
            success=[{"tenant_id": "tenant_1", "plugin_id": "plugin_1"}],
            failed=[],
            skipped=[],
        )

        with patch(
            "framework.clients.inner_http_client.InnerHttpClient.post",
            new_callable=AsyncMock,
            return_value=mock_http_response,
        ):
            client = AIClient(inner_url="http://ai-service:8000")
            result = await client.batch_install_plugins(mock_session, installations)

            assert isinstance(result, BatchInstallResponse)
            assert len(result.success) == 1


class TestAIClientHealthCheck:
    """测试健康检查"""

    @pytest.mark.asyncio
    async def test_health_check_monolithic_mode(self):
        """
        测试单体模式健康检查

        场景：单体模式健康检查
        预期：始终返回 True
        """
        client = AIClient()
        result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_microservice_mode(self):
        """
        测试微服务模式健康检查

        场景：微服务模式健康检查
        预期：调用 HTTP 健康检查接口
        """
        with patch(
            "framework.clients.inner_http_client.InnerHttpClient.health_check",
            new_callable=AsyncMock,
            return_value=True,
        ):
            client = AIClient(inner_url="http://ai-service:8000")
            result = await client.health_check()

            assert result is True


class TestGetAIClient:
    """测试客户端单例工厂"""

    def test_get_ai_client_singleton(self):
        """
        测试获取客户端单例

        场景：多次调用 get_ai_client
        预期：返回同一个实例
        """
        # 清空全局实例
        import framework.clients.ai_client as client_module

        client_module._ai_client = None

        with patch(
            "framework.configs.get_settings",
            return_value=MagicMock(
                ai_inner_url=None,
                ai_inner_timeout=30.0,
            ),
        ):
            client1 = get_ai_client()
            client2 = get_ai_client()

            assert client1 is client2

    def test_get_ai_client_with_config(self):
        """
        测试使用配置创建客户端

        场景：从配置读取 inner_url
        预期：客户端使用配置的 URL
        """
        import framework.clients.ai_client as client_module

        client_module._ai_client = None

        with patch(
            "framework.configs.get_settings",
            return_value=MagicMock(
                ai_inner_url="http://ai-service:8000",
                ai_inner_timeout=60.0,
            ),
        ):
            client = get_ai_client()

            assert client.inner_url == "http://ai-service:8000"


# ==================== Fixtures ====================


@pytest.fixture
def mock_session():
    """Mock 数据库会话"""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session
