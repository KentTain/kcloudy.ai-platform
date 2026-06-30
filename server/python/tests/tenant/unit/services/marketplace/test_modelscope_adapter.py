"""ModelScope 适配器单元测试"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from tenant.services.marketplace.adapters.modelscope_adapter import ModelScopeAdapter
from tenant.services.marketplace.protocol import MarketplaceTestResult


@pytest.fixture
def adapter():
    return ModelScopeAdapter()


# --- 同步方法测试（不需要 @pytest.mark.asyncio）---


def test_market_type(adapter: ModelScopeAdapter):
    assert adapter.market_type == "modelscope"


def test_build_headers_with_token(adapter: ModelScopeAdapter):
    config = {"auth_config": {"api_token": "test-token"}}
    headers = adapter._build_headers(config)
    assert headers["Authorization"] == "Bearer test-token"


def test_build_headers_no_token(adapter: ModelScopeAdapter):
    config = {"auth_config": {}}
    headers = adapter._build_headers(config)
    assert "Authorization" not in headers


def test_build_headers_empty_config(adapter: ModelScopeAdapter):
    """无 auth_config 键时不应抛出异常，且不包含 Authorization"""
    config = {}
    headers = adapter._build_headers(config)
    assert "Authorization" not in headers
    assert headers["Accept"] == "application/json"


def test_parse_datetime_valid(adapter: ModelScopeAdapter):
    result = adapter._parse_datetime("2026-01-15T10:30:00Z")
    assert isinstance(result, datetime)
    assert result.year == 2026


def test_parse_datetime_none(adapter: ModelScopeAdapter):
    assert adapter._parse_datetime(None) is None


def test_parse_datetime_invalid(adapter: ModelScopeAdapter):
    """无效字符串输入应返回 None"""
    assert adapter._parse_datetime("not-a-datetime") is None


def test_parse_model(adapter: ModelScopeAdapter):
    data = {
        "Namespace": "Qwen",
        "Name": "Qwen2.5-72B",
        "ChineseName": "通义千问",
        "Description": "A large model",
        "Version": "1.0.0",
        "Tags": ["chat", "nlp"],
        "Downloads": 10000,
        "CreateTime": "2026-01-15T10:30:00Z",
        "UpdateTime": "2026-06-01T08:00:00Z",
    }
    plugin = adapter._parse_model(data)
    assert plugin.plugin_id == "Qwen/Qwen2.5-72B"
    assert plugin.name == "通义千问"
    assert plugin.author == "Qwen"
    assert plugin.version == "1.0.0"
    assert "chat" in plugin.tags
    assert plugin.downloads == 10000


def test_parse_model_empty_namespace_and_name(adapter: ModelScopeAdapter):
    """namespace 和 name 都为空时应返回 None"""
    data = {"Namespace": "", "Name": ""}
    assert adapter._parse_model(data) is None


def test_parse_model_no_keys(adapter: ModelScopeAdapter):
    """缺少 Namespace 和 Name 键时应返回 None"""
    data = {}
    assert adapter._parse_model(data) is None


def test_parse_model_only_namespace(adapter: ModelScopeAdapter):
    """仅有 namespace 时应正常构建"""
    data = {"Namespace": "Qwen", "Name": ""}
    plugin = adapter._parse_model(data)
    assert plugin is not None
    assert plugin.plugin_id == "Qwen/"


def test_parse_model_only_name(adapter: ModelScopeAdapter):
    """仅有 name 时应正常构建"""
    data = {"Namespace": "", "Name": "Qwen2.5-72B"}
    plugin = adapter._parse_model(data)
    assert plugin is not None
    assert plugin.plugin_id == "/Qwen2.5-72B"


def test_parse_model_no_chinese_name(adapter: ModelScopeAdapter):
    """ChineseName 不存在时回退到 Name"""
    data = {"Namespace": "Qwen", "Name": "Qwen2.5-72B"}
    plugin = adapter._parse_model(data)
    assert plugin is not None
    assert plugin.name == "Qwen2.5-72B"


# --- 异步方法测试 ---


@pytest.mark.asyncio
async def test_test_connection_success(adapter: ModelScopeAdapter):
    """test_connection 成功连接"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Data": {"TotalCount": 42}}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await adapter.test_connection({"auth_config": {}})
    assert isinstance(result, MarketplaceTestResult)
    assert result.success is True
    assert result.plugin_count == 42


@pytest.mark.asyncio
async def test_test_connection_timeout(adapter: ModelScopeAdapter):
    """test_connection 超时"""
    import httpx

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await adapter.test_connection({"auth_config": {}})
    assert result.success is False
    assert "超时" in result.message


@pytest.mark.asyncio
async def test_list_plugins_success(adapter: ModelScopeAdapter):
    """list_plugins 正常返回"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "Data": {
            "Models": [
                {
                    "Namespace": "Qwen",
                    "Name": "Qwen2.5-72B",
                    "ChineseName": "通义千问",
                    "Version": "1.0.0",
                    "Downloads": 100,
                }
            ],
            "TotalCount": 1,
        }
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        plugins, total = await adapter.list_plugins({"auth_config": {}})
    assert total == 1
    assert len(plugins) == 1
    assert plugins[0].plugin_id == "Qwen/Qwen2.5-72B"


@pytest.mark.asyncio
async def test_list_plugins_timeout(adapter: ModelScopeAdapter):
    """list_plugins 超时时返回空列表"""
    import httpx

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        plugins, total = await adapter.list_plugins({"auth_config": {}})
    assert plugins == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_plugins_http_error(adapter: ModelScopeAdapter):
    """list_plugins HTTP 错误时返回空列表"""
    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
    )

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        plugins, total = await adapter.list_plugins({"auth_config": {}})
    assert plugins == []
    assert total == 0


@pytest.mark.asyncio
async def test_get_plugin_success(adapter: ModelScopeAdapter):
    """get_plugin 正常返回"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "Data": {
            "Namespace": "Qwen",
            "Name": "Qwen2.5-72B",
            "ChineseName": "通义千问",
            "Version": "1.0.0",
        }
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        plugin = await adapter.get_plugin({"auth_config": {}}, "Qwen/Qwen2.5-72B")
    assert plugin is not None
    assert plugin.plugin_id == "Qwen/Qwen2.5-72B"


@pytest.mark.asyncio
async def test_get_plugin_not_found(adapter: ModelScopeAdapter):
    """get_plugin 404 时返回 None"""
    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        plugin = await adapter.get_plugin({"auth_config": {}}, "nonexistent/model")
    assert plugin is None
