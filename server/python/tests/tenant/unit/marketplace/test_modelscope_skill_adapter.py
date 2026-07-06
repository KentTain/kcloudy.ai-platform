"""ModelScope Skill 市场适配器单元测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tenant.services.marketplace.adapters.modelscope_skill_adapter import ModelScopeSkillAdapter


@pytest.fixture
def adapter():
    return ModelScopeSkillAdapter()


@pytest.mark.asyncio
async def test_market_type(adapter: ModelScopeSkillAdapter):
    """验证市场类型为 modelscope-skill"""
    assert adapter.market_type == "modelscope-skill"


@pytest.mark.asyncio
async def test_test_connection_success(adapter: ModelScopeSkillAdapter):
    """验证连接测试成功"""
    config = {
        "url": "https://modelscope.cn/api/v1",
        "auth_config": {"api_token": "test-token"}
    }

    # Mock httpx.AsyncClient
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Data": {
            "Skills": [],
            "TotalCount": 10
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await adapter.test_connection(config)

        assert result.success is True
        assert result.message == "连接成功"
        assert result.plugin_count == 10
        assert result.latency_ms is not None


@pytest.mark.asyncio
async def test_list_plugins_success(adapter: ModelScopeSkillAdapter):
    """验证列表获取和字段映射（包括 HasScript→script 转换）"""
    config = {
        "url": "https://modelscope.cn/api/v1",
        "auth_config": {"api_token": "test-token"}
    }

    # Mock API 响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Data": {
            "Skills": [
                {
                    "Id": "author1/skill1",
                    "Name": "Skill 1",
                    "ChineseName": "技能 1",
                    "Description": "A test skill",
                    "Version": "1.0.0",
                    "Owner": "author1",
                    "Tags": ["nlp", "chat"],
                    "Downloads": 100,
                    "Logo": "https://example.com/logo.png",
                    "DownloadUrl": "https://example.com/skill1.zip",
                    "HasScript": True
                },
                {
                    "Id": "author2/skill2",
                    "Name": "Skill 2",
                    "ChineseName": "技能 2",
                    "Description": "Another skill",
                    "Version": "2.0.0",
                    "Owner": "author2",
                    "Tags": ["cv"],
                    "Downloads": 200,
                    "Logo": "https://example.com/logo2.png",
                    "DownloadUrl": "https://example.com/skill2.zip",
                    "HasScript": False
                }
            ],
            "TotalCount": 2
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        plugins, total = await adapter.list_plugins(config)

        assert total == 2
        assert len(plugins) == 2

        # 验证第一个插件（HasScript=True → skill_type="script"）
        plugin1 = plugins[0]
        assert plugin1.plugin_id == "author1/skill1"
        assert plugin1.name == "技能 1"
        assert plugin1.author == "author1"
        assert plugin1.version == "1.0.0"
        assert plugin1.skill_type == "script"
        assert plugin1.downloads == 100

        # 验证第二个插件（HasScript=False → skill_type="knowledge"）
        plugin2 = plugins[1]
        assert plugin2.plugin_id == "author2/skill2"
        assert plugin2.name == "技能 2"
        assert plugin2.skill_type == "knowledge"
        assert plugin2.downloads == 200


@pytest.mark.asyncio
async def test_parse_skill_type_knowledge(adapter: ModelScopeSkillAdapter):
    """验证 HasScript=False → 'knowledge'"""
    data = {
        "Id": "author/skill",
        "Name": "Test Skill",
        "ChineseName": "测试技能",
        "Description": "Test",
        "Version": "1.0.0",
        "Owner": "author",
        "Tags": [],
        "Downloads": 10,
        "DownloadUrl": "https://example.com/skill.zip",
        "HasScript": False
    }

    plugin = adapter._parse_skill(data)

    assert plugin.skill_type == "knowledge"
    assert plugin.plugin_id == "author/skill"


@pytest.mark.asyncio
async def test_parse_skill_type_script(adapter: ModelScopeSkillAdapter):
    """验证 HasScript=True → 'script'"""
    data = {
        "Id": "author/skill",
        "Name": "Test Skill",
        "ChineseName": "测试技能",
        "Description": "Test",
        "Version": "1.0.0",
        "Owner": "author",
        "Tags": [],
        "Downloads": 10,
        "DownloadUrl": "https://example.com/skill.zip",
        "HasScript": True
    }

    plugin = adapter._parse_skill(data)

    assert plugin.skill_type == "script"
    assert plugin.plugin_id == "author/skill"
