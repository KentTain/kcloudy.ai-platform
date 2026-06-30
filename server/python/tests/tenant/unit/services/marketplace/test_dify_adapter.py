"""Dify 适配器单元测试"""

import pytest
from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter


@pytest.fixture
def dify_adapter() -> DifyAdapter:
    return DifyAdapter()


@pytest.mark.asyncio
async def test_market_type(dify_adapter: DifyAdapter):
    """测试市场类型"""
    assert dify_adapter.market_type == "dify"


@pytest.mark.asyncio
async def test_build_headers_no_auth(dify_adapter: DifyAdapter):
    """测试无认证时构建请求头"""
    config = {"auth_type": "none", "auth_config": {}}
    headers = dify_adapter._build_headers(config)
    assert headers == {"Accept": "application/json"}


@pytest.mark.asyncio
async def test_build_headers_api_key(dify_adapter: DifyAdapter):
    """测试 API Key 认证时构建请求头"""
    config = {
        "auth_type": "api_key",
        "auth_config": {"api_key": "test-key", "header_name": "X-API-Key"},
    }
    headers = dify_adapter._build_headers(config)
    assert headers["X-API-Key"] == "test-key"


@pytest.mark.asyncio
async def test_build_headers_token_auth(dify_adapter: DifyAdapter):
    """测试 Token 认证时构建请求头"""
    config = {
        "auth_type": "token",
        "auth_config": {"token": "my-token"},
    }
    headers = dify_adapter._build_headers(config)
    assert headers["Authorization"] == "Bearer my-token"


@pytest.mark.asyncio
async def test_test_connection_empty_url(dify_adapter: DifyAdapter):
    """测试空 URL 时连接测试"""
    config = {"url": ""}
    result = await dify_adapter.test_connection(config)
    assert result.success is False
    assert result.message == "市场地址不能为空"


@pytest.mark.asyncio
async def test_parse_datetime_valid(dify_adapter: DifyAdapter):
    """测试有效日期时间解析"""
    result = dify_adapter._parse_datetime("2024-01-15T10:30:00Z")
    assert result is not None
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15


@pytest.mark.asyncio
async def test_parse_datetime_none(dify_adapter: DifyAdapter):
    """测试空日期时间解析"""
    result = dify_adapter._parse_datetime(None)
    assert result is None


@pytest.mark.asyncio
async def test_parse_datetime_invalid(dify_adapter: DifyAdapter):
    """测试无效日期时间解析"""
    result = dify_adapter._parse_datetime("invalid-date")
    assert result is None


@pytest.mark.asyncio
async def test_parse_plugin(dify_adapter: DifyAdapter):
    """测试插件数据解析"""
    item = {
        "author": "test-author",
        "name": "test-plugin",
        "label": {"en_US": "Test Plugin"},
        "description": {"en_US": "A test plugin"},
        "version": "1.0.0",
        "type": "tool",
        "tags": ["ai", "utility"],
        "downloads": 100,
    }
    base_url = "https://marketplace.example.com"
    result = dify_adapter._parse_plugin(item, base_url)

    assert result.plugin_id == "test-author/test-plugin"
    assert result.name == "Test Plugin"
    assert result.description == "A test plugin"
    assert result.version == "1.0.0"
    assert result.author == "test-author"
    assert result.plugin_type == "tool"
    assert result.tags == ["ai", "utility"]
    assert result.downloads == 100
    assert result.download_url == "https://marketplace.example.com/plugins/test-author/test-plugin/download"


@pytest.mark.asyncio
async def test_parse_plugin_with_id(dify_adapter: DifyAdapter):
    """测试带 ID 的插件数据解析"""
    item = {
        "plugin_id": "custom/plugin-id",
        "author": "test-author",
        "name": "test-plugin",
        "version": "2.0.0",
        "type": "model",
    }
    base_url = "https://marketplace.example.com"
    result = dify_adapter._parse_plugin(item, base_url)

    assert result.plugin_id == "custom/plugin-id"
    assert result.plugin_type == "model"
