"""
Skill 同步流程集成测试

测试从适配器到存储服务到数据库定义的完整同步流程。
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.models.plugin_marketplace import TenantPluginMarketplace
from tenant.services.marketplace.gateway import marketplace_gateway
from tenant.services.marketplace.protocol import RemotePluginInfo


@pytest.fixture
def mock_db_session():
    """Mock 数据库会话"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.scalar_one_or_none = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_marketplace():
    """Mock 市场对象"""
    marketplace = MagicMock(spec=TenantPluginMarketplace)
    marketplace.id = "market-001"
    marketplace.name = "测试市场"
    marketplace.type = "dify"
    marketplace.is_enabled = True
    marketplace.url = "https://marketplace.example.com"
    marketplace.api_key = "test-api-key"
    return marketplace


class TestSkillSyncFlow:
    """Skill 同步流程集成测试"""

    @pytest.mark.asyncio
    async def test_sync_skill_creates_definition(
        self, mock_db_session, mock_marketplace
    ):
        """测试同步 Skill 创建插件定义"""
        # 准备 Mock 数据
        skill_info = RemotePluginInfo(
            plugin_id="community/airtable",
            name="airtable",
            description="Airtable integration",
            version="1.0.0",
            author="community",
            icon=None,
            plugin_type="skill",
            manifest_url=None,
            download_url="https://example.com/download",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            skill_type="knowledge",
            tags=["integration", "database"],
        )

        skill_data = b"fake skill package data"
        checksum = "abc123def456"

        # Mock marketplace_gateway.get_marketplace
        with patch.object(
            marketplace_gateway, "get_marketplace", new_callable=AsyncMock
        ) as mock_get_marketplace:
            mock_get_marketplace.return_value = mock_marketplace

            # Mock 适配器
            mock_adapter = AsyncMock()
            mock_adapter.get_plugin = AsyncMock(return_value=skill_info)
            mock_adapter.download_plugin = AsyncMock(return_value=(skill_data, checksum))

            # Mock _get_adapter
            with patch.object(
                marketplace_gateway, "_get_adapter", return_value=mock_adapter
            ):
                # Mock _build_adapter_config
                with patch.object(
                    marketplace_gateway, "_build_adapter_config", return_value={}
                ):
                    # Mock 存储服务
                    with patch(
                        "tenant.services.plugin_storage_service.plugin_storage_service.upload_skill_package",
                        new_callable=AsyncMock,
                    ) as mock_upload:
                        mock_upload.return_value = "skills/community/airtable/1.0.0/package.zip"

                        # Mock 数据库查询（无现有记录）
                        mock_result = MagicMock()
                        mock_result.scalar_one_or_none.return_value = None
                        mock_db_session.execute.return_value = mock_result

                        # 执行同步
                        result = await marketplace_gateway.sync_skill_from_marketplace(
                            mock_db_session, "market-001", "community/airtable"
                        )

                        # 验证结果
                        assert result is not None
                        assert result.plugin_id == "community/airtable"
                        assert result.skill_type == "knowledge"
                        assert result.runtime_type == "none"
                        assert result.manifest_type == "skill"
                        assert result.source_type == "remote"
                        assert result.install_type == "remote"

                        # 验证 declaration 内容
                        assert "skill" in result.declaration
                        assert result.declaration["skill"]["skill_type"] == "knowledge"
                        assert result.declaration["skill"]["runtime"] == "none"

                        # 验证 session.add 被调用
                        mock_db_session.add.assert_called_once()

                        # 验证 session.flush 被调用
                        mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_skill_updates_existing_definition(
        self, mock_db_session, mock_marketplace
    ):
        """测试同步 Skill 更新现有插件定义"""
        from tenant.models.plugin_definition import TenantPluginDefinition

        # 准备现有插件定义
        existing_def = MagicMock(spec=TenantPluginDefinition)
        existing_def.plugin_id = "community/airtable"
        existing_def.version = "1.0.0"
        existing_def.skill_type = "knowledge"
        existing_def.runtime_type = "none"
        existing_def.remote_version = "1.0.0"
        existing_def.local_version = "1.0.0"
        existing_def.declaration = {
            "skill": {"skill_type": "knowledge", "runtime": "none"}
        }

        # 准备新版 Skill 信息
        skill_info = RemotePluginInfo(
            plugin_id="community/airtable",
            name="airtable",
            description="Airtable integration - Updated",
            version="1.1.0",
            author="community",
            icon=None,
            plugin_type="skill",
            manifest_url=None,
            download_url="https://example.com/download",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            skill_type="knowledge",
            tags=["integration", "database"],
        )

        skill_data = b"fake skill package data v1.1.0"
        checksum = "new_checksum_value"

        # Mock marketplace_gateway.get_marketplace
        with patch.object(
            marketplace_gateway, "get_marketplace", new_callable=AsyncMock
        ) as mock_get_marketplace:
            mock_get_marketplace.return_value = mock_marketplace

            # Mock 适配器
            mock_adapter = AsyncMock()
            mock_adapter.get_plugin = AsyncMock(return_value=skill_info)
            mock_adapter.download_plugin = AsyncMock(return_value=(skill_data, checksum))

            # Mock _get_adapter
            with patch.object(
                marketplace_gateway, "_get_adapter", return_value=mock_adapter
            ):
                # Mock _build_adapter_config
                with patch.object(
                    marketplace_gateway, "_build_adapter_config", return_value={}
                ):
                    # Mock 存储服务
                    with patch(
                        "tenant.services.plugin_storage_service.plugin_storage_service.upload_skill_package",
                        new_callable=AsyncMock,
                    ) as mock_upload:
                        mock_upload.return_value = (
                            "skills/community/airtable/1.1.0/package.zip"
                        )

                        # Mock 数据库查询（返回现有记录）
                        mock_result = MagicMock()
                        mock_result.scalar_one_or_none.return_value = existing_def
                        mock_db_session.execute.return_value = mock_result

                        # 执行同步
                        result = await marketplace_gateway.sync_skill_from_marketplace(
                            mock_db_session, "market-001", "community/airtable"
                        )

                        # 验证结果
                        assert result is existing_def
                        assert result.remote_version == "1.1.0"
                        assert result.skill_type == "knowledge"
                        assert result.runtime_type == "none"

                        # 验证 session.add 未被调用
                        mock_db_session.add.assert_not_called()

                        # 验证 session.flush 被调用
                        mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_skill_with_script_type(self, mock_db_session, mock_marketplace):
        """测试同步脚本类型 Skill"""
        # 准备 Mock 数据
        skill_info = RemotePluginInfo(
            plugin_id="community/calculator",
            name="calculator",
            description="Calculator script",
            version="1.0.0",
            author="community",
            icon=None,
            plugin_type="skill",
            manifest_url=None,
            download_url="https://example.com/download",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            skill_type="script",
            tags=["utility"],
        )

        skill_data = b"fake script package data"
        checksum = "script_checksum"

        # Mock marketplace_gateway.get_marketplace
        with patch.object(
            marketplace_gateway, "get_marketplace", new_callable=AsyncMock
        ) as mock_get_marketplace:
            mock_get_marketplace.return_value = mock_marketplace

            # Mock 适配器
            mock_adapter = AsyncMock()
            mock_adapter.get_plugin = AsyncMock(return_value=skill_info)
            mock_adapter.download_plugin = AsyncMock(return_value=(skill_data, checksum))

            # Mock _get_adapter
            with patch.object(
                marketplace_gateway, "_get_adapter", return_value=mock_adapter
            ):
                # Mock _build_adapter_config
                with patch.object(
                    marketplace_gateway, "_build_adapter_config", return_value={}
                ):
                    # Mock 存储服务
                    with patch(
                        "tenant.services.plugin_storage_service.plugin_storage_service.upload_skill_package",
                        new_callable=AsyncMock,
                    ) as mock_upload:
                        mock_upload.return_value = (
                            "skills/community/calculator/1.0.0/package.zip"
                        )

                        # Mock 数据库查询（无现有记录）
                        mock_result = MagicMock()
                        mock_result.scalar_one_or_none.return_value = None
                        mock_db_session.execute.return_value = mock_result

                        # 执行同步
                        result = await marketplace_gateway.sync_skill_from_marketplace(
                            mock_db_session, "market-001", "community/calculator"
                        )

                        # 验证结果
                        assert result is not None
                        assert result.plugin_id == "community/calculator"
                        assert result.skill_type == "script"
                        assert result.runtime_type == "sandbox"

                        # 验证 declaration 内容
                        assert "skill" in result.declaration
                        assert result.declaration["skill"]["skill_type"] == "script"
                        assert result.declaration["skill"]["runtime"] == "sandbox"

    @pytest.mark.asyncio
    async def test_sync_skill_marketplace_not_found(self, mock_db_session):
        """测试市场不存在时的错误处理"""
        # Mock marketplace_gateway.get_marketplace 返回 None
        with patch.object(
            marketplace_gateway, "get_marketplace", new_callable=AsyncMock
        ) as mock_get_marketplace:
            mock_get_marketplace.return_value = None

            # 执行并验证异常
            with pytest.raises(ValueError, match="市场不存在"):
                await marketplace_gateway.sync_skill_from_marketplace(
                    mock_db_session, "non-existent-market", "community/airtable"
                )

    @pytest.mark.asyncio
    async def test_sync_skill_skill_not_found(self, mock_db_session, mock_marketplace):
        """测试 Skill 不存在时的错误处理"""
        # Mock marketplace_gateway.get_marketplace
        with patch.object(
            marketplace_gateway, "get_marketplace", new_callable=AsyncMock
        ) as mock_get_marketplace:
            mock_get_marketplace.return_value = mock_marketplace

            # Mock 适配器返回 None
            mock_adapter = AsyncMock()
            mock_adapter.get_plugin = AsyncMock(return_value=None)

            # Mock _get_adapter
            with patch.object(
                marketplace_gateway, "_get_adapter", return_value=mock_adapter
            ):
                # Mock _build_adapter_config
                with patch.object(
                    marketplace_gateway, "_build_adapter_config", return_value={}
                ):
                    # 执行并验证异常
                    with pytest.raises(ValueError, match="Skill 不存在"):
                        await marketplace_gateway.sync_skill_from_marketplace(
                            mock_db_session, "market-001", "non-existent/skill"
                        )
