# PluginManagementService 单元测试

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from ai.services.plugin import PluginManagementService


class TestPluginManagementServiceGetList:
    """插件列表查询测试"""

    @pytest.mark.asyncio
    async def test_get_plugin_list_without_tenant_id_raises(self, session):
        """测试缺少租户ID时抛出异常"""
        service = PluginManagementService()

        with patch("ai.services.plugin.get_tenant_id", return_value=None):
            with pytest.raises(ValueError, match="租户ID不能为空"):
                await service.get_plugin_list(session)

    @pytest.mark.asyncio
    async def test_get_plugin_list_with_status_filter(self, session):
        """测试按状态过滤插件列表"""
        service = PluginManagementService()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        session.execute.return_value = mock_result

        with patch("ai.services.plugin.get_tenant_id", return_value="tenant-001"):
            result = await service.get_plugin_list(session, status="active")

            assert result.total == 0
            assert len(result.plugins) == 0


class TestPluginManagementServiceGetInfo:
    """插件详情查询测试"""

    @pytest.mark.asyncio
    async def test_get_plugin_info_without_tenant_id_raises(self, session):
        """测试缺少租户ID时抛出异常"""
        service = PluginManagementService()

        with patch("ai.services.plugin.get_tenant_id", return_value=None):
            with pytest.raises(ValueError, match="租户ID不能为空"):
                await service.get_plugin_info(session, "test-plugin")


class TestPluginManagementServiceCredentials:
    """凭证管理测试"""

    @pytest.mark.asyncio
    async def test_get_credential_not_found_raises(self, session):
        """测试凭证不存在时抛出异常"""
        service = PluginManagementService()

        with patch("ai.models.plugin.PluginCredential.one_by_id", return_value=None):
            with pytest.raises(ValueError, match="凭证不存在"):
                await service.get_credential(session, "nonexistent-cred")
