"""
Tenant-AI 模块依赖重构集成测试

验证重构后的调用链是否正常工作。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestPluginProviderRefactored:
    """测试重构后的 plugin_provider"""

    @pytest.mark.asyncio
    async def test_start_installation_uses_ai_client(self):
        """
        测试 start_installation 使用 AI 客户端

        验证点：
        1. 不再直接导入 ai.services.plugin
        2. 使用 framework.clients.ai_client
        """
        # 导入被测模块
        from tenant.services.plugin_provider import PluginInstallationProviderImpl

        # Mock AI 客户端
        mock_client = MagicMock()
        mock_client.start_plugin = AsyncMock(
            return_value=MagicMock(
                plugin_id="test_plugin",
                message="启动成功",
                status="running",
                success=True,
                process_id=12345,
                port=8080,
            )
        )

        # Mock get_task_session
        mock_session = MagicMock()

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_session_ctx:
            mock_session_ctx.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "framework.clients.ai_client.get_ai_client",
                return_value=mock_client,
            ):
                provider = PluginInstallationProviderImpl()

                # Mock update_installation
                provider.update_installation = AsyncMock(
                    return_value=MagicMock(
                        tenant_id="test_tenant",
                        plugin_id="test_plugin",
                        status="ACTIVE",
                    )
                )

                # 调用方法
                result = await provider.start_installation("test_tenant", "test_plugin")

                # 验证调用了 AI 客户端
                mock_client.start_plugin.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_installation_uses_ai_client(self):
        """
        测试 stop_installation 使用 AI 客户端

        验证点：
        1. 不再直接导入 ai.services.plugin
        2. 使用 framework.clients.ai_client
        """
        from tenant.services.plugin_provider import PluginInstallationProviderImpl

        mock_client = MagicMock()
        mock_client.stop_plugin = AsyncMock(
            return_value=MagicMock(
                plugin_id="test_plugin",
                message="停止成功",
                status="inactive",
                success=True,
            )
        )

        mock_session = MagicMock()

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_session_ctx:
            mock_session_ctx.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "framework.clients.ai_client.get_ai_client",
                return_value=mock_client,
            ):
                provider = PluginInstallationProviderImpl()
                provider.update_installation = AsyncMock(
                    return_value=MagicMock(
                        tenant_id="test_tenant",
                        plugin_id="test_plugin",
                        status="INACTIVE",
                    )
                )

                result = await provider.stop_installation("test_tenant", "test_plugin")

                mock_client.stop_plugin.assert_called_once()


class TestPluginDefinitionServiceRefactored:
    """测试重构后的 plugin_definition_service"""

    @pytest.mark.asyncio
    async def test_install_to_tenants_uses_ai_client(self):
        """
        测试 install_to_tenants 使用 AI 客户端

        验证点：
        1. 不再直接导入 ai.models
        2. 使用 framework.clients.ai_client 批量安装
        """
        from tenant.services.plugin_definition_service import PluginDefinitionService
        from tenant.models.plugin_definition import TenantPluginDefinition
        from tenant.models.tenant import Tenant

        # Mock 数据
        mock_definition = MagicMock(spec=TenantPluginDefinition)
        mock_definition.plugin_id = "test_plugin"
        mock_definition.plugin_unique_identifier = "author/test_plugin"
        mock_definition.declaration = {"name": "Test Plugin"}
        mock_definition.is_enabled = True
        mock_definition.install_type = "local"

        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "test_tenant"

        # Mock AI 客户端返回
        mock_client = MagicMock()
        mock_client.batch_install_plugins = AsyncMock(
            return_value=MagicMock(
                success=[MagicMock(tenant_id="test_tenant", plugin_id="test_plugin")],
                failed=[],
                skipped=[],
            )
        )

        mock_session = MagicMock()
        # 模拟三次查询：插件定义、租户存在、已安装检查
        def_execute = MagicMock()
        def_result = MagicMock()
        def_result.scalar_one_or_none.return_value = mock_definition

        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = mock_tenant

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None  # 未安装

        def_execute.side_effect = [def_result, tenant_result, existing_result]
        mock_session.execute = AsyncMock(side_effect=def_execute.side_effect)

        with patch(
            "framework.clients.ai_client.get_ai_client",
            return_value=mock_client,
        ):
            with patch(
                "framework.tenant.plugin_protocols.get_plugin_installation_provider"
            ) as mock_provider:
                mock_provider_instance = MagicMock()
                mock_provider_instance.create_installation = AsyncMock()
                mock_provider.return_value = mock_provider_instance

                service = PluginDefinitionService()

                # Mock request
                mock_request = MagicMock()
                mock_request.tenant_ids = ["test_tenant"]
                mock_request.auto_start = False

                # 调用方法
                result = await service.install_to_tenants(
                    mock_session, "test_plugin", mock_request
                )

                # 验证调用了 AI 客户端的批量安装方法
                mock_client.batch_install_plugins.assert_called_once()


class TestDependencyVerification:
    """验证依赖关系改进"""

    def test_tenant_not_import_ai_service_directly(self):
        """
        测试 Tenant 模块不再直接导入 AI Service

        验证点：检查导入语句
        """
        # 读取 plugin_provider.py 源码
        with open(
            "src/tenant/services/plugin_provider.py", "r", encoding="utf-8"
        ) as f:
            content = f.read()

        # 验证不包含直接导入 ai.services.plugin
        assert "from ai.services.plugin import" not in content
        assert "import ai.services.plugin" not in content

    def test_tenant_not_import_ai_models_directly(self):
        """
        测试 Tenant 模块不再直接导入 AI Model

        验证点：检查导入语句
        """
        with open(
            "src/tenant/services/plugin_definition_service.py", "r", encoding="utf-8"
        ) as f:
            content = f.read()

        # 验证不包含直接导入 ai.models
        assert "from ai.models.plugin_config import" not in content
        assert "from ai.models.plugin_runtime_state import" not in content

    def test_tenant_uses_ai_client(self):
        """
        测试 Tenant 模块使用 AI 客户端

        验证点：检查导入语句
        """
        with open(
            "src/tenant/services/plugin_provider.py", "r", encoding="utf-8"
        ) as f:
            content = f.read()

        # 验证使用 framework.clients.ai_client
        assert "from framework.clients.ai_client import" in content

        with open(
            "src/tenant/services/plugin_definition_service.py", "r", encoding="utf-8"
        ) as f:
            content = f.read()

        assert "from framework.clients.ai_client import" in content
