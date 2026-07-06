"""AgentSkills 适配器单元测试"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tenant.services.marketplace.adapters.agentskills_adapter import (
    AgentSkillsAdapter,
)
from tenant.services.marketplace.protocol import RemotePluginInfo


@pytest.fixture
def agentskills_adapter() -> AgentSkillsAdapter:
    return AgentSkillsAdapter()


@pytest.mark.asyncio
async def test_market_type(agentskills_adapter: AgentSkillsAdapter):
    """测试市场类型"""
    assert agentskills_adapter.market_type == "agentskills"


@pytest.mark.asyncio
async def test_list_plugins_success(agentskills_adapter: AgentSkillsAdapter):
    """测试列表获取和字段映射"""
    config = {"url": "https://agentskills.io"}

    # Mock response data
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "skills": [
            {
                "identifier": "test-author/test-skill",
                "name": "Test Skill",
                "description": "A test skill",
                "version": "1.0.0",
                "author": "test-author",
                "tags": ["ai", "knowledge"],
                "download_url": "https://agentskills.io/skills/test-author/test-skill/download",
            }
        ],
        "total": 1,
    }

    # Mock AsyncClient
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        plugins, total = await agentskills_adapter.list_plugins(config)

        # 验证返回值
        assert total == 1
        assert len(plugins) == 1

        plugin = plugins[0]
        assert isinstance(plugin, RemotePluginInfo)
        assert plugin.plugin_id == "test-author/test-skill"
        assert plugin.name == "Test Skill"
        assert plugin.description == "A test skill"
        assert plugin.version == "1.0.0"
        assert plugin.author == "test-author"
        assert plugin.tags == ["ai", "knowledge"]
        assert plugin.plugin_type == "skill"
        assert plugin.skill_type == "knowledge"

        # 验证 API 调用
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "https://agentskills.io/api/v1/skills"
        assert call_args[1]["params"]["page"] == 1
        assert call_args[1]["params"]["size"] == 20


@pytest.mark.asyncio
async def test_list_plugins_with_pagination(agentskills_adapter: AgentSkillsAdapter):
    """测试分页参数传递"""
    config = {"url": "https://agentskills.io"}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"skills": [], "total": 100}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        plugins, total = await agentskills_adapter.list_plugins(
            config, page=3, page_size=50
        )

        # 验证分页参数
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["page"] == 3
        assert call_args[1]["params"]["size"] == 50
        assert total == 100


@pytest.mark.asyncio
async def test_download_plugin_success(agentskills_adapter: AgentSkillsAdapter):
    """测试下载和 SHA256 校验"""
    config = {"url": "https://agentskills.io"}
    plugin_id = "test-author/test-skill"

    # Mock response data
    test_data = b"test plugin content"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = test_data

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        data, checksum = await agentskills_adapter.download_plugin(
            config, plugin_id, version="1.0.0"
        )

        # 验证下载内容
        assert data == test_data
        assert len(checksum) == 64  # SHA256 hex digest length

        # 验证 API 调用
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert (
            call_args[0][0]
            == "https://agentskills.io/api/v1/skills/test-author/test-skill/download"
        )
        assert call_args[1]["params"]["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_test_connection_success(agentskills_adapter: AgentSkillsAdapter):
    """测试连接测试"""
    config = {"url": "https://agentskills.io"}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"skills": [], "total": 42}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await agentskills_adapter.test_connection(config)

        # 验证测试结果
        assert result.success is True
        assert result.message == "连接成功"
        assert result.plugin_count == 42
        assert result.latency_ms is not None
        assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_get_plugin_success(agentskills_adapter: AgentSkillsAdapter):
    """测试单个 Skill 获取"""
    config = {"url": "https://agentskills.io"}
    plugin_id = "test-author/test-skill"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "identifier": "test-author/test-skill",
        "name": "Test Skill",
        "description": "A test skill",
        "version": "2.0.0",
        "author": "test-author",
        "tags": ["knowledge"],
        "download_url": "https://agentskills.io/skills/test-author/test-skill/download",
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        plugin = await agentskills_adapter.get_plugin(config, plugin_id)

        # 验证返回值
        assert plugin is not None
        assert isinstance(plugin, RemotePluginInfo)
        assert plugin.plugin_id == "test-author/test-skill"
        assert plugin.name == "Test Skill"
        assert plugin.version == "2.0.0"
        assert plugin.plugin_type == "skill"
        assert plugin.skill_type == "knowledge"

        # 验证 API 调用
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert (
            call_args[0][0]
            == "https://agentskills.io/api/v1/skills/test-author/test-skill"
        )
