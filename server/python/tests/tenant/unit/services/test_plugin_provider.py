"""
PluginInstallationProvider 单元测试

测试 PluginInstallationProviderImpl 的 CRUD 操作和引用计数机制。
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework.tenant.plugin_protocols import PluginInstallationDTO
from tenant.services.plugin_provider import PluginInstallationProviderImpl


@pytest.fixture
def provider():
    """Provider 实例"""
    return PluginInstallationProviderImpl()


@pytest.fixture
def sample_dto():
    """示例插件安装 DTO"""
    return PluginInstallationDTO(
        tenant_id="tenant-001",
        plugin_id="author/plugin-name",
        plugin_unique_identifier="author/plugin-name:1.0.0@abc123",
        declaration={
            "version": "1.0.0",
            "name": "plugin-name",
            "author": "author",
            "tools_configuration": [],
        },
        status="PENDING",
        freeze_threshold_hours=24,
        plugin_type="local",
        runtime_type="python",
    )


class TestCreateInstallation:
    """创建安装记录测试"""

    @pytest.mark.asyncio
    async def test_create_installation_with_declaration(self, provider, sample_dto):
        """测试创建安装记录（包含 declaration）"""
        # 模拟数据库会话
        mock_session = AsyncMock()
        mock_definition = MagicMock()
        mock_definition.refers = 0
        mock_definition.plugin_id = sample_dto.plugin_id
        mock_definition.plugin_unique_identifier = sample_dto.plugin_unique_identifier

        mock_installation = MagicMock()
        mock_installation.tenant_id = sample_dto.tenant_id
        mock_installation.plugin_id = sample_dto.plugin_id
        mock_installation.plugin_unique_identifier = sample_dto.plugin_unique_identifier
        mock_installation.status = "PENDING"
        mock_installation.freeze_threshold_hours = sample_dto.freeze_threshold_hours
        mock_installation.plugin_type = sample_dto.plugin_type
        mock_installation.runtime_type = sample_dto.runtime_type

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # 模拟 TenantPluginDefinition.one_by_field
            with patch(
                "tenant.models.plugin_definition.TenantPluginDefinition.one_by_field",
                return_value=None,
            ):
                # 模拟 session.add 和 session.flush
                mock_session.add = MagicMock()
                mock_session.flush = AsyncMock()

                # 模拟 TenantPluginInstallation 的构造
                with patch(
                    "tenant.models.plugin_installation.TenantPluginInstallation"
                ) as mock_installation_class:
                    mock_installation_class.return_value = mock_installation

                    result = await provider.create_installation(
                        "tenant-001", sample_dto
                    )

                    # 验证返回值
                    assert result is not None
                    assert result.tenant_id == "tenant-001"
                    assert result.plugin_id == "author/plugin-name"

    @pytest.mark.asyncio
    async def test_create_installation_increments_refers(self, provider, sample_dto):
        """测试创建安装记录时引用计数递增"""
        mock_session = AsyncMock()

        # 模拟已存在的插件定义
        mock_definition = MagicMock()
        mock_definition.refers = 1
        mock_definition.plugin_id = sample_dto.plugin_id
        mock_definition.plugin_unique_identifier = sample_dto.plugin_unique_identifier

        mock_installation = MagicMock()
        mock_installation.tenant_id = sample_dto.tenant_id
        mock_installation.plugin_id = sample_dto.plugin_id
        mock_installation.plugin_unique_identifier = sample_dto.plugin_unique_identifier
        mock_installation.status = "PENDING"
        mock_installation.freeze_threshold_hours = sample_dto.freeze_threshold_hours
        mock_installation.plugin_type = sample_dto.plugin_type
        mock_installation.runtime_type = sample_dto.runtime_type

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # 模拟 TenantPluginDefinition.one_by_field 返回已存在的定义
            with patch(
                "tenant.models.plugin_definition.TenantPluginDefinition.one_by_field",
                return_value=mock_definition,
            ):
                mock_session.flush = AsyncMock()

                with patch(
                    "tenant.models.plugin_installation.TenantPluginInstallation"
                ) as mock_installation_class:
                    mock_installation_class.return_value = mock_installation

                    await provider.create_installation("tenant-001", sample_dto)

                    # 验证引用计数递增
                    assert mock_definition.refers == 2
                    mock_session.flush.assert_called()


class TestUpdateInstallation:
    """更新安装记录测试"""

    @pytest.mark.asyncio
    async def test_update_installation_status(self, provider, sample_dto):
        """测试更新安装状态"""
        mock_session = AsyncMock()

        mock_installation = MagicMock()
        mock_installation.tenant_id = "tenant-001"
        mock_installation.plugin_id = "author/plugin-name"
        mock_installation.plugin_unique_identifier = sample_dto.plugin_unique_identifier
        mock_installation.status = "PENDING"
        mock_installation.freeze_threshold_hours = 24
        mock_installation.plugin_type = "local"
        mock_installation.runtime_type = "python"

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=mock_installation,
            ):
                mock_installation.update = AsyncMock()

                result = await provider.update_installation(
                    "tenant-001", "author/plugin-name", {"status": "ACTIVE"}
                )

                # 验证 update 方法被调用
                mock_installation.update.assert_called_once_with(
                    mock_session, {"status": "ACTIVE"}
                )

    @pytest.mark.asyncio
    async def test_update_installation_not_found(self, provider):
        """测试更新不存在的安装记录"""
        mock_session = AsyncMock()

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=None,
            ):
                with pytest.raises(ValueError, match="安装记录不存在"):
                    await provider.update_installation(
                        "tenant-001", "author/plugin-name", {"status": "ACTIVE"}
                    )


class TestDeleteInstallation:
    """删除安装记录测试"""

    @pytest.mark.asyncio
    async def test_delete_installation(self, provider):
        """测试删除安装记录"""
        mock_session = AsyncMock()

        mock_installation = MagicMock()
        mock_installation.tenant_id = "tenant-001"
        mock_installation.plugin_id = "author/plugin-name"

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=mock_installation,
            ):
                mock_installation.delete = AsyncMock()

                await provider.delete_installation("tenant-001", "author/plugin-name")

                mock_installation.delete.assert_called_once_with(mock_session)

    @pytest.mark.asyncio
    async def test_delete_installation_not_found(self, provider):
        """测试删除不存在的安装记录"""
        mock_session = AsyncMock()

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=None,
            ):
                with pytest.raises(ValueError, match="安装记录不存在"):
                    await provider.delete_installation(
                        "tenant-001", "author/plugin-name"
                    )


class TestGetTenantInstallations:
    """获取租户安装记录测试"""

    @pytest.mark.asyncio
    async def test_get_tenant_installations(self, provider, sample_dto):
        """测试获取租户的所有安装记录"""
        mock_session = AsyncMock()

        mock_installation1 = MagicMock()
        mock_installation1.tenant_id = "tenant-001"
        mock_installation1.plugin_id = "author/plugin-1"
        mock_installation1.plugin_unique_identifier = "author/plugin-1:1.0.0@abc123"
        mock_installation1.status = "ACTIVE"
        mock_installation1.freeze_threshold_hours = 24
        mock_installation1.plugin_type = "local"
        mock_installation1.runtime_type = "python"

        mock_installation2 = MagicMock()
        mock_installation2.tenant_id = "tenant-001"
        mock_installation2.plugin_id = "author/plugin-2"
        mock_installation2.plugin_unique_identifier = "author/plugin-2:1.0.0@def456"
        mock_installation2.status = "PENDING"
        mock_installation2.freeze_threshold_hours = 24
        mock_installation2.plugin_type = "remote"
        mock_installation2.runtime_type = "nodejs"

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.all_by_field",
                return_value=[mock_installation1, mock_installation2],
            ):
                result = await provider.get_tenant_installations("tenant-001")

                assert len(result) == 2
                assert result[0].plugin_id == "author/plugin-1"
                assert result[1].plugin_id == "author/plugin-2"

    @pytest.mark.asyncio
    async def test_get_tenant_installations_empty(self, provider):
        """测试租户无安装记录"""
        mock_session = AsyncMock()

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.all_by_field",
                return_value=[],
            ):
                result = await provider.get_tenant_installations("tenant-001")

                assert len(result) == 0


class TestGetInstallation:
    """获取单个安装记录测试"""

    @pytest.mark.asyncio
    async def test_get_installation(self, provider):
        """测试获取单个安装记录"""
        mock_session = AsyncMock()

        mock_installation = MagicMock()
        mock_installation.tenant_id = "tenant-001"
        mock_installation.plugin_id = "author/plugin-name"
        mock_installation.plugin_unique_identifier = "author/plugin-name:1.0.0@abc123"
        mock_installation.status = "ACTIVE"
        mock_installation.freeze_threshold_hours = 24
        mock_installation.plugin_type = "local"
        mock_installation.runtime_type = "python"

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=mock_installation,
            ):
                result = await provider.get_installation(
                    "tenant-001", "author/plugin-name"
                )

                assert result is not None
                assert result.plugin_id == "author/plugin-name"

    @pytest.mark.asyncio
    async def test_get_installation_not_found(self, provider):
        """测试获取不存在的安装记录"""
        mock_session = AsyncMock()

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
                return_value=None,
            ):
                result = await provider.get_installation(
                    "tenant-001", "author/plugin-name"
                )

                assert result is None
