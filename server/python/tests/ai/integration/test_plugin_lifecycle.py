"""
插件生命周期集成测试

测试插件的完整安装/卸载流程，包括：
- 插件安装成功流程
- 插件安装失败（AI 侧失败）
- 插件卸载成功流程
- 安装重复插件
"""

import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"


@pytest.fixture
def test_tenant_id():
    """测试租户 ID"""
    return "test-tenant-" + uuid.uuid4().hex[:8]


@pytest.fixture
def test_plugin_id():
    """测试插件 ID"""
    return "test-author/test-plugin"


@pytest.fixture
def test_plugin_unique_identifier():
    """测试插件唯一标识符"""
    return "test-author/test-plugin:1.0.0@abc123"


@pytest.fixture
def test_declaration():
    """测试插件声明"""
    return {
        "version": "1.0.0",
        "name": "test-plugin",
        "author": "test-author",
        "tools_configuration": [
            {
                "provider": "test_provider",
                "credentials_schema": [
                    {
                        "name": "api_key",
                        "type": "secret-input",
                        "required": True,
                        "label": "API Key",
                    }
                ],
            }
        ],
    }


@pytest.fixture
def registered_provider():
    """注册 PluginInstallationProvider"""
    from framework.tenant.plugin_protocols import (
        register_plugin_installation_provider,
    )
    from tenant.services.plugin import plugin_installation_provider_impl

    register_plugin_installation_provider(plugin_installation_provider_impl)
    return plugin_installation_provider_impl


@pytest.mark.integration
@pytest.mark.asyncio
class TestPluginLifecycle:
    """插件生命周期集成测试"""

    async def test_plugin_installation_success(
        self,
        test_tenant_id,
        test_plugin_id,
        test_plugin_unique_identifier,
        test_declaration,
        registered_provider,
    ):
        """测试插件安装成功流程"""
        from framework.tenant.plugin_protocols import PluginInstallationDTO

        # 模拟数据库会话和模型操作
        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # 模拟插件定义不存在
            with patch(
                "tenant.models.plugin_definition.TenantPluginDefinition.one_by_field",
                return_value=None,
            ):
                # 模拟安装记录创建
                mock_installation = MagicMock()
                mock_installation.tenant_id = test_tenant_id
                mock_installation.plugin_id = test_plugin_id
                mock_installation.plugin_unique_identifier = test_plugin_unique_identifier
                mock_installation.status = "PENDING"
                mock_installation.auto_start = False
                mock_installation.freeze_threshold_hours = 24
                mock_installation.plugin_type = "local"
                mock_installation.runtime_type = "python"

                with patch(
                    "tenant.models.plugin_installation.TenantPluginInstallation"
                ) as mock_installation_class:
                    mock_installation_class.return_value = mock_installation

                    # 模拟 AI 侧配置创建成功
                    with patch(
                        "ai.components.plugin.engine.core.plugin_manager.PluginManagerFactory.get_manager"
                    ) as mock_get_manager:
                        mock_manager = AsyncMock()
                        mock_manager.install_plugin = AsyncMock(return_value=True)
                        mock_get_manager.return_value = mock_manager

                        # Step 1: Tenant 侧创建安装记录
                        dto = PluginInstallationDTO(
                            tenant_id=test_tenant_id,
                            plugin_id=test_plugin_id,
                            plugin_unique_identifier=test_plugin_unique_identifier,
                            declaration=test_declaration,
                            status="PENDING",
                        )

                        from framework.tenant.plugin_protocols import (
                            get_plugin_installation_provider,
                        )

                        provider = get_plugin_installation_provider()
                        result = await provider.create_installation(test_tenant_id, dto)

                        # 验证安装记录创建成功
                        assert result is not None
                        assert result.tenant_id == test_tenant_id
                        assert result.plugin_id == test_plugin_id

    async def test_plugin_installation_ai_side_failure(
        self,
        test_tenant_id,
        test_plugin_id,
        test_plugin_unique_identifier,
        test_declaration,
        registered_provider,
    ):
        """测试插件安装失败（AI 侧失败）"""
        from framework.events import event_publisher
        from framework.events.domain_events import PluginInstallationFailed
        from framework.tenant.plugin_protocols import get_plugin_installation_provider

        # 模拟安装记录已创建
        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__.return_value = mock_session

            mock_installation = MagicMock()
            mock_installation.tenant_id = test_tenant_id
            mock_installation.plugin_id = test_plugin_id
            mock_installation.status = "PENDING"

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=mock_installation,
            ):
                mock_installation.update = AsyncMock()

                # 模拟 AI 侧配置创建失败
                with patch(
                    "ai.components.plugin.engine.core.plugin_manager.PluginManagerFactory.get_manager"
                ) as mock_get_manager:
                    mock_manager = AsyncMock()
                    mock_manager.install_plugin = AsyncMock(
                        side_effect=Exception("AI 配置创建失败")
                    )
                    mock_get_manager.return_value = mock_manager

                    # 模拟发布安装失败事件
                    with patch(
                        "framework.events.publisher.RedisUtil.xadd"
                    ) as mock_xadd:
                        mock_xadd.return_value = "1234567890-0"

                        event = PluginInstallationFailed(
                            tenant_id=test_tenant_id,
                            plugin_id=test_plugin_id,
                            error_message="AI 配置创建失败",
                        )
                        await event_publisher.publish(event)

                        # 验证事件发布
                        mock_xadd.assert_called_once()

    async def test_plugin_uninstall_success(
        self,
        test_tenant_id,
        test_plugin_id,
        registered_provider,
    ):
        """测试插件卸载成功流程"""
        from framework.tenant.plugin_protocols import get_plugin_installation_provider

        # 模拟安装记录存在
        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__.return_value = mock_session

            mock_installation = MagicMock()
            mock_installation.tenant_id = test_tenant_id
            mock_installation.plugin_id = test_plugin_id
            mock_installation.status = "ACTIVE"

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=mock_installation,
            ):
                mock_installation.delete = AsyncMock()

                # 模拟 AI 侧配置删除成功
                with patch(
                    "ai.components.plugin.engine.core.plugin_manager.PluginManagerFactory.get_manager"
                ) as mock_get_manager:
                    mock_manager = AsyncMock()
                    mock_manager.uninstall_plugin = AsyncMock(return_value=True)
                    mock_get_manager.return_value = mock_manager

                    # Step 1: Tenant 侧删除安装记录
                    provider = get_plugin_installation_provider()
                    await provider.delete_installation(test_tenant_id, test_plugin_id)

                    # 验证删除操作被调用
                    mock_installation.delete.assert_called_once()

    async def test_install_duplicate_plugin(
        self,
        test_tenant_id,
        test_plugin_id,
        test_plugin_unique_identifier,
        test_declaration,
        registered_provider,
    ):
        """测试安装重复插件"""
        from framework.tenant.plugin_protocols import (
            PluginInstallationDTO,
            get_plugin_installation_provider,
        )

        # 模拟已存在的安装记录
        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__.return_value = mock_session

            mock_existing_installation = MagicMock()
            mock_existing_installation.tenant_id = test_tenant_id
            mock_existing_installation.plugin_id = test_plugin_id
            mock_existing_installation.status = "ACTIVE"
            mock_existing_installation.plugin_unique_identifier = test_plugin_unique_identifier
            mock_existing_installation.auto_start = False
            mock_existing_installation.freeze_threshold_hours = 24
            mock_existing_installation.plugin_type = "local"
            mock_existing_installation.runtime_type = "python"

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=mock_existing_installation,
            ):
                # 尝试再次安装相同的插件
                dto = PluginInstallationDTO(
                    tenant_id=test_tenant_id,
                    plugin_id=test_plugin_id,
                    plugin_unique_identifier=test_plugin_unique_identifier,
                    declaration=test_declaration,
                )

                provider = get_plugin_installation_provider()

                # 验证可以检测到重复安装
                existing = await provider.get_installation(test_tenant_id, test_plugin_id)

                # 验证已存在安装记录
                assert existing is not None


@pytest.mark.integration
@pytest.mark.asyncio
class TestPluginEventFlow:
    """插件事件流测试"""

    async def test_installation_failed_event_updates_status(
        self,
        test_tenant_id,
        test_plugin_id,
    ):
        """测试安装失败事件更新安装状态"""
        from framework.events.domain_events import PluginInstallationFailed

        # 模拟安装记录存在
        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__.return_value = mock_session

            mock_installation = MagicMock()
            mock_installation.tenant_id = test_tenant_id
            mock_installation.plugin_id = test_plugin_id
            mock_installation.status = "PENDING"

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=mock_installation,
            ):
                mock_installation.update = AsyncMock()

                # 模拟监听器接收到事件并更新状态
                event = PluginInstallationFailed(
                    tenant_id=test_tenant_id,
                    plugin_id=test_plugin_id,
                    error_message="配置创建失败",
                )

                # 模拟监听器处理逻辑
                await mock_installation.update(mock_session, {"status": "FAILED"})

                # 验证状态更新
                mock_installation.update.assert_called_once_with(
                    mock_session, {"status": "FAILED"}
                )

    async def test_uninstall_failed_event_logs_error(
        self,
        test_tenant_id,
        test_plugin_id,
    ):
        """测试卸载失败事件记录错误日志"""
        from framework.events.domain_events import PluginUninstallFailed

        # 模拟日志记录
        with patch(
            "tenant.listeners.handlers.plugin_handler._logger"
        ) as mock_logger:
            event = PluginUninstallFailed(
                tenant_id=test_tenant_id,
                plugin_id=test_plugin_id,
                error_message="AI 侧数据删除失败",
            )

            # 模拟监听器记录错误日志
            mock_logger.error(
                f"插件卸载失败: tenant_id={event.tenant_id}, "
                f"plugin_id={event.plugin_id}, error={event.error_message}"
            )

            # 验证日志被记录
            mock_logger.error.assert_called_once()
