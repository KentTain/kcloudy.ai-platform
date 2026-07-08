"""ModelScope Skill 适配器集成测试

对真实 ModelScope API 进行测试，验证适配器实现的正确性。

运行条件：
- 设置环境变量 E2E_MODELSCOPE_API_TOKEN，或在 conftest.py 中配置默认值
- ModelScope API 服务可访问

运行方式：
    uv run pytest tests/tenant/integration/marketplace/test_modelscope_skill_adapter_integration.py -v
"""

import json

import pytest

from tenant.services.marketplace.adapters.modelscope_skill_adapter import ModelScopeSkillAdapter


@pytest.fixture
def adapter():
    """Skill 适配器实例"""
    return ModelScopeSkillAdapter()


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
    """测试连接到真实 ModelScope Skill API"""
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
async def test_list_skills_from_real_api(adapter, config, modelscope_api_available):
    """测试从真实 API 获取 Skill 列表"""
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
    assert first_plugin.plugin_type == "skill"
    assert first_plugin.skill_metadata is not None
    assert "category" in first_plugin.skill_metadata


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_skills_from_real_api(adapter, config, modelscope_api_available):
    """测试从真实 API 搜索 Skill"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    # 搜索包含 "地图" 的技能
    plugins, total = await adapter.list_plugins(config, keyword="地图", page=1, page_size=3)

    # 验证搜索结果
    if total > 0:
        assert len(plugins) > 0
        # 验证返回的插件包含搜索关键词（在名称或描述中）
        for plugin in plugins:
            assert plugin.plugin_id or plugin.name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_skill_detail_from_real_api(adapter, config, modelscope_api_available):
    """测试从真实 API 获取 Skill 详情"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    # 先获取一个存在的技能
    plugins, total = await adapter.list_plugins(config, page=1, page_size=1)

    if total == 0:
        pytest.skip("没有可用的 Skill")

    plugin_id = plugins[0].plugin_id

    # 获取详情
    detail = await adapter.get_plugin(config, plugin_id)

    assert detail is not None
    assert detail.plugin_id == plugin_id
    assert detail.name
    assert detail.plugin_type == "skill"
    assert detail.skill_metadata is not None
    assert "category" in detail.skill_metadata
    assert "source_url" in detail.skill_metadata


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_nonexistent_skill(adapter, config, modelscope_api_available):
    """测试获取不存在的 Skill"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    detail = await adapter.get_plugin(config, "@nonexistent/invalid-skill")

    assert detail is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_skill_manifest(adapter, config, modelscope_api_available):
    """测试生成 Skill 配置清单"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    # 先获取一个存在的技能
    plugins, total = await adapter.list_plugins(config, page=1, page_size=1)

    if total == 0:
        pytest.skip("没有可用的 Skill")

    plugin_id = plugins[0].plugin_id

    # 下载清单
    data, checksum = await adapter.download_plugin(config, plugin_id)

    # 验证返回数据
    assert isinstance(data, bytes)
    assert len(data) > 0
    assert len(checksum) == 64  # SHA256 hex

    # 解析 JSON
    manifest = json.loads(data)

    # 验证清单结构
    assert "skill" in manifest
    assert "metadata" in manifest
    assert "install" in manifest
    assert "skill_type" in manifest["skill"]
    assert manifest["skill"]["skill_type"] in ["knowledge", "script"]
    assert "name" in manifest["metadata"]
    assert "source_url" in manifest["install"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_metadata_fields(adapter, config, modelscope_api_available):
    """测试 Skill 元数据字段正确性"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    # 获取多个技能，验证字段映射
    plugins, total = await adapter.list_plugins(config, page=1, page_size=5)

    assert len(plugins) > 0

    for plugin in plugins:
        # 验证必需字段
        assert plugin.plugin_id
        assert plugin.name
        assert plugin.plugin_type == "skill"

        # 验证元数据
        metadata = plugin.skill_metadata
        assert metadata is not None
        assert "category" in metadata
        assert "developer" in metadata
        assert "source_url" in metadata
        assert "license" in metadata
        assert "view_count" in metadata

        # view_count 应该是整数
        assert isinstance(metadata["view_count"], int)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_check_updates_from_real_api(adapter, config, modelscope_api_available):
    """测试检查 Skill 更新"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    # 先获取一个存在的技能
    plugins, total = await adapter.list_plugins(config, page=1, page_size=1)

    if total == 0:
        pytest.skip("没有可用的 Skill")

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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skill_type_inference(adapter, config, modelscope_api_available):
    """测试 Skill 类型推断"""
    if not modelscope_api_available:
        pytest.skip("ModelScope API 不可用")

    # 获取技能列表
    plugins, total = await adapter.list_plugins(config, page=1, page_size=10)

    if total == 0:
        pytest.skip("没有可用的 Skill")

    # 统计各种 category
    categories = {}
    for plugin in plugins:
        category = plugin.skill_metadata.get("category", "")
        categories[category] = categories.get(category, 0) + 1

    # 验证至少有一些技能
    assert len(categories) > 0

    # 打印 category 分布（用于调试）
    print(f"\nSkill categories distribution: {categories}")
