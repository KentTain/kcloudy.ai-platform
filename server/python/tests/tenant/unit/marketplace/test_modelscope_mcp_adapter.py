"""ModelScope MCP 市场适配器单元测试（符合官方 OpenAPI 规范）"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tenant.services.marketplace.adapters.modelscope_mcp_adapter import ModelScopeMcpAdapter


@pytest.fixture
def adapter():
    return ModelScopeMcpAdapter()


@pytest.mark.asyncio
async def test_market_type(adapter: ModelScopeMcpAdapter):
    """验证市场类型为 modelscope-mcp"""
    assert adapter.market_type == "modelscope-mcp"


@pytest.mark.asyncio
async def test_test_connection_success(adapter: ModelScopeMcpAdapter):
    """验证连接测试成功（使用 PUT 方法）"""
    config = {
        "url": "https://modelscope.cn/openapi/v1",
        "auth_config": {"api_token": "test-token"},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    # 官方 API 返回格式：data.total_count
    mock_response.json.return_value = {"data": {"mcp_server_list": [], "total_count": 5}}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        # 适配器现在使用 PUT 方法
        mock_client.put.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await adapter.test_connection(config)

        assert result.success is True
        assert result.message == "连接成功"
        assert result.plugin_count == 5
        assert result.latency_ms is not None


@pytest.mark.asyncio
async def test_test_connection_failure(adapter: ModelScopeMcpAdapter):
    """验证连接测试失败时返回失败结果"""
    config = {"url": "https://modelscope.cn/openapi/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.put.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await adapter.test_connection(config)

        assert result.success is False
        assert "HTTP 500" in result.message


@pytest.mark.asyncio
async def test_list_plugins_success(adapter: ModelScopeMcpAdapter):
    """验证列表获取与字段映射（使用 PUT 方法，官方字段名）"""
    config = {"url": "https://modelscope.cn/openapi/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 200
    # 官方 API 返回格式
    mock_response.json.return_value = {
        "data": {
            "mcp_server_list": [
                {
                    "id": "@author1/mcp1",
                    "name": "mcp1",
                    "chinese_name": "MCP 服务 1",
                    "description": "A test MCP server",
                    "publisher": "@author1/mcp1",
                    "tags": ["search", "tools"],
                    "view_count": 42,
                    "logo_url": "https://example.com/logo.png",
                },
                {
                    "id": "@author2/mcp2",
                    "name": "mcp2",
                    "chinese_name": "MCP 服务 2",
                    "description": "Another MCP server",
                    "publisher": "@author2/mcp2",
                    "tags": [],
                    "view_count": 7,
                },
            ],
            "total_count": 2,
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.put.return_value = mock_response
        mock_client_class.return_value = mock_client

        plugins, total = await adapter.list_plugins(config)

    assert total == 2
    assert len(plugins) == 2

    plugin1 = plugins[0]
    assert plugin1.plugin_id == "@author1/mcp1"
    assert plugin1.name == "MCP 服务 1"
    assert plugin1.author == "@author1/mcp1"
    assert plugin1.plugin_type == "mcp"
    assert plugin1.downloads == 42

    plugin2 = plugins[1]
    assert plugin2.plugin_id == "@author2/mcp2"
    assert plugin2.plugin_type == "mcp"


@pytest.mark.asyncio
async def test_get_plugin_found(adapter: ModelScopeMcpAdapter):
    """验证获取单个 MCP server 详情（带连接信息）"""
    config = {"url": "https://modelscope.cn/openapi/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 200
    # 官方 API 详情返回格式（含 operational_urls）
    mock_response.json.return_value = {
        "data": {
            "id": "@author/mcp",
            "name": "mcp",
            "chinese_name": "测试 MCP",
            "description": "desc",
            "author": "author",
            "publisher": "@author/mcp",
            "tags": [],
            "view_count": 3,
            "operational_urls": [
                {
                    "url": "https://mcp.api-inference.modelscope.net/xxxx/mcp",
                    "transport_type": "sse",
                    "auth_required": False,
                }
            ],
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        plugin = await adapter.get_plugin(config, "@author/mcp")

    assert plugin is not None
    assert plugin.plugin_id == "@author/mcp"
    assert plugin.plugin_type == "mcp"
    assert plugin.download_url == "https://mcp.api-inference.modelscope.net/xxxx/mcp"
    assert plugin.skill_metadata.get("transport_type") == "sse"


@pytest.mark.asyncio
async def test_get_plugin_not_found(adapter: ModelScopeMcpAdapter):
    """验证 404 时返回 None"""
    config = {"url": "https://modelscope.cn/openapi/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        plugin = await adapter.get_plugin(config, "missing/mcp")

    assert plugin is None


@pytest.mark.asyncio
async def test_download_plugin_returns_manifest_and_checksum(adapter: ModelScopeMcpAdapter):
    """验证 download_plugin 返回连接清单 JSON 与 SHA256 校验和"""
    config = {"url": "https://modelscope.cn/openapi/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "id": "@author/mcp",
            "name": "mcp",
            "chinese_name": "测试 MCP",
            "description": "desc",
            "author": "author",
            "publisher": "@author/mcp",
            "tags": ["search"],
            "view_count": 1,
            "operational_urls": [
                {
                    "url": "https://mcp.api-inference.modelscope.net/xxxx/mcp",
                    "transport_type": "sse",
                    "auth_required": False,
                }
            ],
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        data, checksum = await adapter.download_plugin(config, "@author/mcp")

    manifest = json.loads(data)
    assert manifest["mcp"]["server_url"] == "https://mcp.api-inference.modelscope.net/xxxx/mcp"
    assert manifest["mcp"]["transport"] == "sse"
    assert manifest["metadata"]["name"] == "测试 MCP"
    assert len(checksum) == 64  # SHA256 hex


@pytest.mark.asyncio
async def test_download_plugin_raises_when_missing(adapter: ModelScopeMcpAdapter):
    """验证 MCP server 不存在时 download_plugin 抛出异常"""
    config = {"url": "https://modelscope.cn/openapi/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(ValueError, match="not found"):
            await adapter.download_plugin(config, "missing/mcp")


@pytest.mark.asyncio
async def test_check_updates_detects_version_diff(adapter: ModelScopeMcpAdapter):
    """验证更新检查能识别版本差异"""
    config = {"url": "https://modelscope.cn/openapi/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "id": "@author/mcp",
            "name": "MCP",
            "chinese_name": "MCP",
            "description": "",
            "author": "author",
            "publisher": "@author/mcp",
            "tags": [],
            "view_count": 0,
            "operational_urls": [],
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
            [{"plugin_id": "@author/mcp", "current_version": "1.0.0"}],
        )

    assert len(results) == 1
    assert results[0].has_update is True  # latest vs 1.0.0
    assert results[0].latest_version == "latest"
