"""ModelScope Skill 市场适配器单元测试（符合官方 OpenAPI 规范）"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
        "url": "https://modelscope.cn/openapi/v1",
        "auth_config": {"api_token": "test-token"},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    # 官方 API 返回格式
    mock_response.json.return_value = {
        "data": {
            "skills": [],
            "total": 10,
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
    """验证列表获取和字段映射（官方字段名）"""
    config = {
        "url": "https://modelscope.cn/openapi/v1",
        "auth_config": {"api_token": "test-token"},
    }

    # Mock API 响应（官方格式）
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "skills": [
                {
                    "id": "@author1/skill1",
                    "display_name": "技能 1",
                    "description": "A test skill",
                    "owner": "author1",
                    "developer": "author1",
                    "category": "developer-tools",
                    "tags": ["category:developer-tools", "custom_tag:nlp"],
                    "downloads": 100,
                    "logo_url": "https://example.com/logo.png",
                    "source_url": "https://github.com/author1/skill1",
                },
                {
                    "id": "@author2/skill2",
                    "display_name": "技能 2",
                    "description": "Another skill",
                    "owner": "author2",
                    "category": "ai-media",
                    "tags": ["category:ai-media"],
                    "downloads": 200,
                    "logo_url": "https://example.com/logo2.png",
                    "source_url": "",
                }
            ],
            "total": 2,
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

        # 验证第一个插件
        plugin1 = plugins[0]
        assert plugin1.plugin_id == "@author1/skill1"
        assert plugin1.name == "技能 1"
        assert plugin1.author == "author1"
        assert plugin1.downloads == 100
        assert plugin1.skill_metadata.get("category") == "developer-tools"

        # 验证第二个插件
        plugin2 = plugins[1]
        assert plugin2.plugin_id == "@author2/skill2"
        assert plugin2.name == "技能 2"
        assert plugin2.downloads == 200


@pytest.mark.asyncio
async def test_parse_skill_fields(adapter: ModelScopeSkillAdapter):
    """验证字段映射正确性"""
    data = {
        "id": "@author/skill",
        "display_name": "测试技能",
        "description": "Test",
        "owner": "author",
        "developer": "dev",
        "category": "developer-tools",
        "tags": ["category:developer-tools"],
        "downloads": 10,
        "logo_url": "https://example.com/logo.png",
        "source_url": "https://github.com/author/skill",
        "license": "MIT",
        "view_count": 100,
        "last_modified": "2026-06-23T17:59:54Z",
    }

    plugin = adapter._parse_skill(data)

    assert plugin.plugin_id == "@author/skill"
    assert plugin.name == "测试技能"
    assert plugin.author == "author"
    assert plugin.downloads == 10
    assert plugin.skill_metadata.get("category") == "developer-tools"
    assert plugin.skill_metadata.get("developer") == "dev"
    assert plugin.skill_metadata.get("source_url") == "https://github.com/author/skill"


@pytest.mark.asyncio
async def test_download_plugin_generates_manifest(adapter: ModelScopeSkillAdapter):
    """验证 download_plugin 生成声明清单（无下载文件）"""
    config = {
        "url": "https://modelscope.cn/openapi/v1",
        "auth_config": {},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "id": "@author/skill",
            "display_name": "测试技能",
            "description": "desc",
            "owner": "author",
            "category": "developer-tools",
            "tags": ["category:developer-tools"],
            "downloads": 1,
            "source_url": "https://github.com/author/skill",
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        data, checksum = await adapter.download_plugin(config, "@author/skill")

    manifest = json.loads(data)
    assert "skill" in manifest
    assert manifest["skill"]["skill_type"] == "script"  # 非 knowledge 类别
    assert manifest["metadata"]["name"] == "测试技能"
    assert manifest["install"]["source_url"] == "https://github.com/author/skill"
    assert len(checksum) == 64  # SHA256 hex


@pytest.mark.asyncio
async def test_infer_skill_type_knowledge(adapter: ModelScopeSkillAdapter):
    """验证 knowledge 类别的推断"""
    assert adapter._infer_skill_type("knowledge-base") == "knowledge"
    assert adapter._infer_skill_type("documentation") == "knowledge"


@pytest.mark.asyncio
async def test_infer_skill_type_script(adapter: ModelScopeSkillAdapter):
    """验证其他类别的推断为 script"""
    assert adapter._infer_skill_type("developer-tools") == "script"
    assert adapter._infer_skill_type("ai-media") == "script"
    assert adapter._infer_skill_type("") == "script"


@pytest.mark.asyncio
async def test_check_updates_detects_version_diff(adapter: ModelScopeSkillAdapter):
    """验证更新检查能识别版本差异"""
    config = {
        "url": "https://modelscope.cn/openapi/v1",
        "auth_config": {},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "id": "@author/skill",
            "display_name": "Skill",
            "description": "",
            "owner": "author",
            "category": "developer-tools",
            "tags": [],
            "downloads": 0,
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        results = await adapter.check_updates(
            config,
            [{"plugin_id": "@author/skill", "current_version": "1.0.0"}],
        )

    assert len(results) == 1
    assert results[0].has_update is True  # latest vs 1.0.0
    assert results[0].latest_version == "latest"
