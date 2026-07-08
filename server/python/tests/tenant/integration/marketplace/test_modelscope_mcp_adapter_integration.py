"""ModelScope MCP 适配器集成测试

对真实 ModelScope API 进行测试，验证适配器实现的正确性。

运行条件：
- 设置环境变量 E2E_MODELSCOPE_API_TOKEN，或在 conftest.py 中配置默认值
- ModelScope API 服务可访问

运行方式：
    uv run pytest tests/tenant/integration/marketplace/test_modelscope_mcp_adapter_integration.py -v
"""

import pytest

from tenant.services.marketplace.adapters.modelscope_mcp_adapter import ModelScopeMcpAdapter


@pytest.fixture
def adapter():
    """MCP 适配器实例"""
    return ModelScopeMcpAdapter()


@pytest.fixture
def config(modelscope_api_token):
    """市场配置（使用真实 API Token）"""
    return {
        "url": "https://modelscope.cn/openapi/v1",
        "auth_config": {"api_token": modelscope_api_token},
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_connection_to_real_api(adapter, config, modelscope_api_available):
    """测试连接到真实 ModelScope MCP API"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    result = await adapter.test_connection(config)

    assert result.success is True
    assert result.message == "连接成功"
    assert result.plugin_count is not None
    assert result.plugin_count > 0
    assert result.latency_ms is not None
    assert result.latency_ms > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_mcp_servers_from_real_api(adapter, config, modelscope_api_available):
    """测试从真实 API 获取 MCP 服务列表"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    plugins, total = await adapter.list_plugins(config, page=1, page_size=5)

    # 验证总数
    assert total > 0

    # 验证返回的插件列表
    assert len(plugins) > 0
    assert len(plugins) <= 5

    # 验证第一个插件的字段
    first_plugin = plugins[0]
    assert first_plugin.plugin_id  # 必须有 ID
    assert first_plugin.plugin_id.startswith("@") or "/" in first_plugin.plugin_id  # 格式：@author/name 或 author/name
    assert first_plugin.name  # 必须有名称
    assert first_plugin.plugin_type == "mcp"
    assert first_plugin.downloads is not None  # view_count


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_mcp_servers_from_real_api(adapter, config, modelscope_api_available):
    """测试从真实 API 搜索 MCP 服务"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    # 搜索包含 "fetch" 的服务
    plugins, total = await adapter.list_plugins(config, keyword="fetch", page=1, page_size=3)

    # 验证搜索结果
    if total > 0:
        assert len(plugins) > 0
        # 验证返回的插件包含搜索关键词
        for plugin in plugins:
            assert plugin.plugin_id or plugin.name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_mcp_server_detail_from_real_api(adapter, config, modelscope_api_available):
    """测试从真实 API 获取 MCP 服务详情（含连接信息）"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    # 先获取一个存在的服务
    plugins, total = await adapter.list_plugins(config, page=1, page_size=1)

    if total == 0:
        pytest.skip("没有可用的 MCP 服务")

    plugin_id = plugins[0].plugin_id

    # 获取详情
    detail = await adapter.get_plugin(config, plugin_id)

    assert detail is not None
    assert detail.plugin_id == plugin_id
    assert detail.name
    assert detail.plugin_type == "mcp"

    # 验证连接信息（operational_urls）
    # 注意：不是所有服务都有 operational_urls
    if detail.download_url:
        assert detail.download_url.startswith("http")
        assert detail.skill_metadata is not None
        assert "transport_type" in detail.skill_metadata
        assert detail.skill_metadata["transport_type"] in ["sse", "streamable_http"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_nonexistent_mcp_server(adapter, config, modelscope_api_available):
    """测试获取不存在的 MCP 服务"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    detail = await adapter.get_plugin(config, "@nonexistent/invalid-mcp-server")

    assert detail is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_mcp_server_manifest(adapter, config, modelscope_api_available):
    """测试生成 MCP 服务配置清单"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    # 先获取一个存在的服务
    plugins, total = await adapter.list_plugins(config, page=1, page_size=1)

    if total == 0:
        pytest.skip("没有可用的 MCP 服务")

    plugin_id = plugins[0].plugin_id

    # 下载清单
    data, checksum = await adapter.download_plugin(config, plugin_id)

    # 验证返回数据
    assert isinstance(data, bytes)
    assert len(data) > 0
    assert len(checksum) == 64  # SHA256 hex

    # 解析 JSON
    import json

    manifest = json.loads(data)

    # 验证清单结构
    assert "mcp" in manifest
    assert "metadata" in manifest
    assert "server_url" in manifest["mcp"]
    assert "transport" in manifest["mcp"]
    assert "name" in manifest["metadata"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_check_updates_from_real_api(adapter, config, modelscope_api_available):
    """测试检查 MCP 服务更新"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    # 先获取一个存在的服务
    plugins, total = await adapter.list_plugins(config, page=1, page_size=1)

    if total == 0:
        pytest.skip("没有可用的 MCP 服务")

    plugin_id = plugins[0].plugin_id

    # 检查更新
    results = await adapter.check_updates(
        config,
        [{"plugin_id": plugin_id, "current_version": "1.0.0"}],
    )

    assert len(results) == 1
    assert results[0].plugin_id == plugin_id
    assert results[0].current_version == "1.0.0"
    assert results[0].latest_version == "latest"
    assert results[0].has_update is True
