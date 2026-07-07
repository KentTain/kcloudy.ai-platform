"""ModelScope MCP 市场适配器单元测试"""

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
    """验证连接测试成功"""
    config = {
        "url": "https://modelscope.cn/api/v1",
        "auth_config": {"api_token": "test-token"},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Data": {"McpServers": [], "TotalCount": 5}}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await adapter.test_connection(config)

        assert result.success is True
        assert result.message == "连接成功"
        assert result.plugin_count == 5
        assert result.latency_ms is not None


@pytest.mark.asyncio
async def test_test_connection_failure(adapter: ModelScopeMcpAdapter):
    """验证连接测试失败时返回失败结果"""
    config = {"url": "https://modelscope.cn/api/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await adapter.test_connection(config)

        assert result.success is False
        assert "HTTP 500" in result.message


@pytest.mark.asyncio
async def test_list_plugins_success(adapter: ModelScopeMcpAdapter):
    """验证列表获取与字段映射（plugin_type 固定为 mcp，ServerUrl → download_url）"""
    config = {"url": "https://modelscope.cn/api/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Data": {
            "McpServers": [
                {
                    "Id": "author1/mcp1",
                    "Name": "mcp1",
                    "ChineseName": "MCP 服务 1",
                    "Description": "A test MCP server",
                    "Version": "1.0.0",
                    "Owner": "author1",
                    "Tags": ["search", "tools"],
                    "Downloads": 42,
                    "Logo": "https://example.com/logo.png",
                    "ServerUrl": "https://mcp.example.com/server1",
                    "Transport": "streamable_http",
                },
                {
                    "Id": "author2/mcp2",
                    "Name": "mcp2",
                    "ChineseName": "MCP 服务 2",
                    "Description": "Another MCP server",
                    "Version": "2.0.0",
                    "Owner": "author2",
                    "Tags": [],
                    "Downloads": 7,
                    "ServerUrl": "wss://mcp.example.com/server2",
                },
            ],
            "TotalCount": 2,
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

    plugin1 = plugins[0]
    assert plugin1.plugin_id == "author1/mcp1"
    assert plugin1.name == "MCP 服务 1"
    assert plugin1.author == "author1"
    assert plugin1.version == "1.0.0"
    assert plugin1.plugin_type == "mcp"
    assert plugin1.download_url == "https://mcp.example.com/server1"
    assert plugin1.downloads == 42

    plugin2 = plugins[1]
    assert plugin2.plugin_id == "author2/mcp2"
    assert plugin2.plugin_type == "mcp"
    assert plugin2.download_url == "wss://mcp.example.com/server2"


@pytest.mark.asyncio
async def test_get_plugin_found(adapter: ModelScopeMcpAdapter):
    """验证获取单个 MCP server 详情"""
    config = {"url": "https://modelscope.cn/api/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Data": {
            "Id": "author/mcp",
            "Name": "mcp",
            "ChineseName": "测试 MCP",
            "Description": "desc",
            "Version": "1.2.0",
            "Owner": "author",
            "Tags": [],
            "Downloads": 3,
            "ServerUrl": "https://mcp.example.com/s",
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        plugin = await adapter.get_plugin(config, "author/mcp")

    assert plugin is not None
    assert plugin.plugin_id == "author/mcp"
    assert plugin.plugin_type == "mcp"
    assert plugin.download_url == "https://mcp.example.com/s"


@pytest.mark.asyncio
async def test_get_plugin_not_found(adapter: ModelScopeMcpAdapter):
    """验证 404 时返回 None"""
    config = {"url": "https://modelscope.cn/api/v1", "auth_config": {}}

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
    config = {"url": "https://modelscope.cn/api/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Data": {
            "Id": "author/mcp",
            "Name": "mcp",
            "ChineseName": "测试 MCP",
            "Description": "desc",
            "Version": "1.0.0",
            "Owner": "author",
            "Tags": ["search"],
            "Downloads": 1,
            "ServerUrl": "https://mcp.example.com/s",
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        data, checksum = await adapter.download_plugin(config, "author/mcp")

    manifest = json.loads(data)
    assert manifest["mcp"]["server_url"] == "https://mcp.example.com/s"
    assert manifest["mcp"]["transport"] == "streamable_http"
    assert manifest["metadata"]["name"] == "测试 MCP"
    assert len(checksum) == 64  # SHA256 hex


@pytest.mark.asyncio
async def test_download_plugin_raises_when_missing(adapter: ModelScopeMcpAdapter):
    """验证 MCP server 不存在时 download_plugin 抛出异常"""
    config = {"url": "https://modelscope.cn/api/v1", "auth_config": {}}

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


def test_extract_transport_websocket(adapter: ModelScopeMcpAdapter):
    """验证 wss:// URL 推导为 websocket"""
    info = MagicMock()
    info.download_url = "wss://mcp.example.com/s"
    assert adapter._extract_transport(info) == "websocket"


def test_extract_transport_sse(adapter: ModelScopeMcpAdapter):
    """验证 /sse URL 推导为 sse"""
    info = MagicMock()
    info.download_url = "https://mcp.example.com/sse"
    assert adapter._extract_transport(info) == "sse"


def test_extract_transport_streamable_http(adapter: ModelScopeMcpAdapter):
    """验证普通 HTTP URL 推导为 streamable_http"""
    info = MagicMock()
    info.download_url = "https://mcp.example.com/server"
    assert adapter._extract_transport(info) == "streamable_http"


@pytest.mark.asyncio
async def test_check_updates_detects_version_diff(adapter: ModelScopeMcpAdapter):
    """验证更新检查能识别版本差异"""
    config = {"url": "https://modelscope.cn/api/v1", "auth_config": {}}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Data": {
            "Id": "author/mcp",
            "Name": "mcp",
            "ChineseName": "MCP",
            "Description": "",
            "Version": "2.0.0",
            "Owner": "author",
            "Tags": [],
            "Downloads": 0,
            "ServerUrl": "https://mcp.example.com/s",
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
            [{"plugin_id": "author/mcp", "current_version": "1.0.0"}],
        )

    assert len(results) == 1
    assert results[0].has_update is True
    assert results[0].latest_version == "2.0.0"
