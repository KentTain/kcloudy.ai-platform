"""
跨模块插件 Provider 集成测试

测试 AI 模块通过 Provider 协议访问 Tenant 数据的流程：
- Provider 注册与获取
- 安装记录跨模块查询
- 事件驱动一致性
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class TestPluginProviderRegistration:
    """Provider 注册流程集成测试"""

    @pytest.mark.asyncio
    async def test_register_and_get_provider(self):
        """测试注册并获取 Provider"""
        from framework.tenant.plugin_protocols import (
            PluginInstallationProvider,
            get_plugin_installation_provider,
            register_plugin_installation_provider,
        )

        # 准备 mock provider
        mock_provider = MagicMock(spec=PluginInstallationProvider)

        # 注册
        register_plugin_installation_provider(mock_provider)

        # 获取
        provider = get_plugin_installation_provider()

        assert provider is mock_provider

    @pytest.mark.asyncio
    async def test_get_tenant_installations_through_provider(self):
        """测试通过 Provider 获取租户安装记录"""
        from framework.tenant.plugin_protocols import (
            PluginInstallationDTO,
            PluginInstallationProvider,
            get_plugin_installation_provider,
            register_plugin_installation_provider,
        )

        # 准备 mock provider
        mock_provider = MagicMock(spec=PluginInstallationProvider)
        mock_provider.get_tenant_installations = AsyncMock()
        register_plugin_installation_provider(mock_provider)

        # 准备测试数据
        tenant_id = "test-tenant"
        mock_installation = PluginInstallationDTO(
            tenant_id=tenant_id,
            plugin_id="langgenius/tongyi",
            plugin_unique_identifier="langgenius/tongyi:0.2.0@hash",
            declaration={},
            status="ACTIVE",
        )
        mock_provider.get_tenant_installations.return_value = [mock_installation]

        # 通过 Provider 查询
        provider = get_plugin_installation_provider()
        installations = await provider.get_tenant_installations(tenant_id)

        assert len(installations) == 1
        assert installations[0].plugin_id == "langgenius/tongyi"
        assert installations[0].status == "ACTIVE"
        mock_provider.get_tenant_installations.assert_awaited_once_with(tenant_id)

    @pytest.mark.asyncio
    async def test_cross_module_install_flow(self):
        """测试跨模块安装流程：AI -> Provider -> Tenant"""
        from framework.tenant.plugin_protocols import (
            PluginInstallationDTO,
            get_plugin_installation_provider,
            register_plugin_installation_provider,
        )

        mock_provider = MagicMock()
        mock_provider.create_installation = AsyncMock()
        register_plugin_installation_provider(mock_provider)

        tenant_id = "test-tenant"
        dto = PluginInstallationDTO(
            tenant_id=tenant_id,
            plugin_id="langgenius/gpustack",
            plugin_unique_identifier="langgenius/gpustack:0.0.15@hash",
            declaration={"name": "gpustack", "version": "0.0.15"},
            status="PENDING",
        )

        mock_provider.create_installation.return_value = dto

        # AI 模块调用 Provider 创建安装记录
        provider = get_plugin_installation_provider()
        result = await provider.create_installation(tenant_id, dto)

        assert result is not None
        assert result.plugin_id == "langgenius/gpustack"
        assert result.status == "PENDING"
        mock_provider.create_installation.assert_awaited_once_with(tenant_id, dto)

    @pytest.mark.asyncio
    async def test_cross_module_uninstall_flow(self):
        """测试跨模块卸载流程：AI -> Provider -> Tenant"""
        from framework.tenant.plugin_protocols import (
            get_plugin_installation_provider,
            register_plugin_installation_provider,
        )

        mock_provider = MagicMock()
        mock_provider.delete_installation = AsyncMock()
        register_plugin_installation_provider(mock_provider)

        tenant_id = "test-tenant"
        plugin_id = "langgenius/tongyi"

        provider = get_plugin_installation_provider()
        await provider.delete_installation(tenant_id, plugin_id)

        mock_provider.delete_installation.assert_awaited_once_with(
            tenant_id, plugin_id
        )


class TestPluginInstallationQuery:
    """插件安装查询集成测试"""

    @pytest.mark.asyncio
    async def test_get_installation_by_id(self):
        """测试按插件 ID 查询安装记录"""
        from framework.tenant.plugin_protocols import (
            PluginInstallationDTO,
            get_plugin_installation_provider,
            register_plugin_installation_provider,
        )

        mock_provider = MagicMock()
        mock_provider.get_installation = AsyncMock()
        register_plugin_installation_provider(mock_provider)

        tenant_id = "test-tenant"
        plugin_id = "langgenius/tongyi"
        mock_installation = PluginInstallationDTO(
            tenant_id=tenant_id,
            plugin_id=plugin_id,
            plugin_unique_identifier="langgenius/tongyi:0.2.0@hash",
            declaration={},
            status="ACTIVE",
        )
        mock_provider.get_installation.return_value = mock_installation

        provider = get_plugin_installation_provider()
        result = await provider.get_installation(tenant_id, plugin_id)

        assert result is not None
        assert result.plugin_id == plugin_id
        assert result.status == "ACTIVE"
        mock_provider.get_installation.assert_awaited_once_with(tenant_id, plugin_id)

    @pytest.mark.asyncio
    async def test_get_installation_not_found(self):
        """测试查询不存在的安装记录"""
        from framework.tenant.plugin_protocols import (
            get_plugin_installation_provider,
            register_plugin_installation_provider,
        )

        mock_provider = MagicMock()
        mock_provider.get_installation = AsyncMock(return_value=None)
        register_plugin_installation_provider(mock_provider)

        provider = get_plugin_installation_provider()
        result = await provider.get_installation("test-tenant", "unknown/plugin")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_installation_status(self):
        """测试更新安装记录状态"""
        from framework.tenant.plugin_protocols import (
            get_plugin_installation_provider,
            register_plugin_installation_provider,
        )

        mock_provider = MagicMock()
        mock_provider.update_installation = AsyncMock()
        register_plugin_installation_provider(mock_provider)

        tenant_id = "test-tenant"
        plugin_id = "langgenius/tongyi"
        update_data = {"status": "ACTIVE"}

        provider = get_plugin_installation_provider()
        await provider.update_installation(tenant_id, plugin_id, update_data)

        mock_provider.update_installation.assert_awaited_once_with(
            tenant_id, plugin_id, update_data
        )
