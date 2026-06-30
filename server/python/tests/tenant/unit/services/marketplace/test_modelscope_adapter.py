"""ModelScope 适配器单元测试"""

import pytest
from datetime import datetime
from tenant.services.marketplace.adapters.modelscope_adapter import ModelScopeAdapter


@pytest.fixture
def adapter():
    return ModelScopeAdapter()


@pytest.mark.asyncio
async def test_market_type(adapter: ModelScopeAdapter):
    assert adapter.market_type == "modelscope"


@pytest.mark.asyncio
async def test_build_headers_with_token(adapter: ModelScopeAdapter):
    config = {"auth_config": {"api_token": "test-token"}}
    headers = adapter._build_headers(config)
    assert headers["Authorization"] == "Bearer test-token"


@pytest.mark.asyncio
async def test_build_headers_no_token(adapter: ModelScopeAdapter):
    config = {"auth_config": {}}
    headers = adapter._build_headers(config)
    assert "Authorization" not in headers


@pytest.mark.asyncio
async def test_parse_datetime_valid(adapter: ModelScopeAdapter):
    result = adapter._parse_datetime("2026-01-15T10:30:00Z")
    assert isinstance(result, datetime)
    assert result.year == 2026


@pytest.mark.asyncio
async def test_parse_datetime_none(adapter: ModelScopeAdapter):
    assert adapter._parse_datetime(None) is None


@pytest.mark.asyncio
async def test_parse_model(adapter: ModelScopeAdapter):
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
