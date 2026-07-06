"""本地文件 Plugin 扫描适配器测试"""

import hashlib
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from tenant.services.marketplace.adapters.local_plugin_adapter import LocalPluginAdapter


def _make_plugin_zip(
    plugin_id: str = "testuser/test-plugin",
    name: str = "Test Plugin",
    version: str = "1.0.0",
    author: str = "testuser",
    manifest_type: str = "tool",
) -> bytes:
    """构造一个最简的插件 ZIP 包"""
    manifest = {
        "version": version,
        "type": manifest_type,
        "author": author,
        "name": plugin_id.split("/")[-1] if "/" in plugin_id else plugin_id,
        "description": {"en_US": f"Description of {name}"},
        "icon": "test.svg",
        "label": {"en_US": name},
        "created_at": "2026-01-01T00:00:00Z",
        "resource": {"memory": 0, "cpu": 0},
        "plugins": {"tools": ["tools/test.yaml"]},
        "meta": {
            "version": "0.1.0",
            "arch": ["amd64"],
            "runner": {"language": "python", "version": "3.12", "entrypoint": "main"},
        },
    }

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.yaml", "")
    data = buf.getvalue()
    return data


class TestLocalPluginAdapter:
    """LocalPluginAdapter 测试"""

    def test_market_type(self):
        """验证市场类型为 local-plugin"""
        adapter = LocalPluginAdapter()
        assert adapter.market_type == "local-plugin"

    def test_parse_url_with_file_prefix(self):
        """验证 file:// 前缀解析"""
        adapter = LocalPluginAdapter()
        result = adapter._parse_url("file:///data/plugins")
        assert result == Path("/data/plugins")

    def test_parse_url_without_prefix(self):
        """验证无前缀路径解析"""
        adapter = LocalPluginAdapter()
        result = adapter._parse_url("/data/plugins")
        assert result == Path("/data/plugins")

    @pytest.mark.asyncio
    async def test_test_connection_success(self, tmp_path: Path):
        """验证连接成功"""
        adapter = LocalPluginAdapter()
        # 空目录也算连接成功
        config = {"url": str(tmp_path)}
        result = await adapter.test_connection(config)
        assert result.success is True
        assert result.plugin_count == 0

    @pytest.mark.asyncio
    async def test_test_connection_empty_url(self):
        """验证空 URL 连接失败"""
        adapter = LocalPluginAdapter()
        config = {"url": ""}
        result = await adapter.test_connection(config)
        assert result.success is False
        assert "不能为空" in result.message

    @pytest.mark.asyncio
    async def test_test_connection_nonexistent_path(self):
        """验证不存在的路径连接失败"""
        adapter = LocalPluginAdapter()
        config = {"url": "/nonexistent/path/12345"}
        result = await adapter.test_connection(config)
        assert result.success is False
        assert "不存在" in result.message

    @pytest.mark.asyncio
    async def test_test_connection_not_directory(self, tmp_path: Path):
        """验证非目录路径连接失败"""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("hello")
        adapter = LocalPluginAdapter()
        config = {"url": str(file_path)}
        result = await adapter.test_connection(config)
        assert result.success is False
        assert "不是目录" in result.message

    @pytest.mark.asyncio
    async def test_list_plugins_empty_directory(self, tmp_path: Path):
        """验证空目录返回空列表"""
        adapter = LocalPluginAdapter()
        config = {"url": str(tmp_path)}
        plugins, total = await adapter.list_plugins(config)
        assert total == 0
        assert len(plugins) == 0

    @pytest.mark.asyncio
    async def test_list_plugins_with_zip(self, tmp_path: Path):
        """验证扫描 ZIP 文件返回插件列表"""
        zip_data = _make_plugin_zip()
        zip_path = tmp_path / "test_plugin.zip"
        zip_path.write_bytes(zip_data)

        mock_info = MagicMock()
        mock_info.plugin_id = "testuser/test-plugin"
        mock_info.name = "Test Plugin"
        mock_info.version = "1.0.0"
        mock_info.author = "testuser"
        mock_info.manifest_type = "tool"
        mock_info.declaration = {
            "tools_configuration": [{"name": "test_tool"}],
            "models_configuration": [],
            "agent_strategies_configuration": [],
        }

        with patch(
            "tenant.services.plugin_package_service.plugin_package_service"
        ) as mock_svc:
            mock_svc.parse_package_from_bytes.return_value = mock_info
            adapter = LocalPluginAdapter()
            config = {"url": str(tmp_path)}
            plugins, total = await adapter.list_plugins(config)

        assert total == 1
        assert len(plugins) == 1
        plugin = plugins[0]
        assert plugin.plugin_id == "testuser/test-plugin"
        assert plugin.name == "Test Plugin"
        assert plugin.version == "1.0.0"
        assert plugin.author == "testuser"
        assert plugin.plugin_type == "tool"

    @pytest.mark.asyncio
    async def test_list_plugins_keyword_filter(self, tmp_path: Path):
        """验证关键词搜索过滤"""
        zip_data = _make_plugin_zip(name="SearchTarget")
        zip_path = tmp_path / "plugin1.zip"
        zip_path.write_bytes(zip_data)

        mock_info = MagicMock()
        mock_info.plugin_id = "test/search-target"
        mock_info.name = "SearchTarget"
        mock_info.version = "1.0.0"
        mock_info.author = "test"
        mock_info.manifest_type = "tool"
        mock_info.declaration = {
            "tools_configuration": [{"name": "tool1"}],
            "models_configuration": [],
            "agent_strategies_configuration": [],
        }

        with patch(
            "tenant.services.plugin_package_service.plugin_package_service"
        ) as mock_svc:
            mock_svc.parse_package_from_bytes.return_value = mock_info
            adapter = LocalPluginAdapter()
            config = {"url": str(tmp_path)}

            # 匹配关键词
            plugins, total = await adapter.list_plugins(config, keyword="SearchTarget")
            assert total == 1

            # 不匹配关键词
            plugins, total = await adapter.list_plugins(config, keyword="nonexistent")
            assert total == 0

    @pytest.mark.asyncio
    async def test_get_plugin_found(self, tmp_path: Path):
        """验证 get_plugin 找到指定插件"""
        zip_data = _make_plugin_zip()
        zip_path = tmp_path / "plugin1.zip"
        zip_path.write_bytes(zip_data)

        mock_info = MagicMock()
        mock_info.plugin_id = "testuser/test-plugin"
        mock_info.name = "Test Plugin"
        mock_info.version = "1.0.0"
        mock_info.author = "testuser"
        mock_info.manifest_type = "tool"
        mock_info.declaration = {
            "tools_configuration": [{"name": "tool1"}],
            "models_configuration": [],
            "agent_strategies_configuration": [],
        }

        with patch(
            "tenant.services.plugin_package_service.plugin_package_service"
        ) as mock_svc:
            mock_svc.parse_package_from_bytes.return_value = mock_info
            adapter = LocalPluginAdapter()
            config = {"url": str(tmp_path)}
            plugin = await adapter.get_plugin(config, "testuser/test-plugin")

        assert plugin is not None
        assert plugin.plugin_id == "testuser/test-plugin"

    @pytest.mark.asyncio
    async def test_get_plugin_not_found(self, tmp_path: Path):
        """验证 get_plugin 未找到返回 None"""
        adapter = LocalPluginAdapter()
        config = {"url": str(tmp_path)}
        plugin = await adapter.get_plugin(config, "nonexistent/plugin")
        assert plugin is None

    @pytest.mark.asyncio
    async def test_download_plugin(self, tmp_path: Path):
        """验证下载插件返回字节和校验和"""
        zip_data = _make_plugin_zip()
        zip_path = tmp_path / "plugin1.zip"
        zip_path.write_bytes(zip_data)

        mock_info = MagicMock()
        mock_info.plugin_id = "testuser/test-plugin"
        mock_info.name = "Test Plugin"
        mock_info.version = "1.0.0"
        mock_info.author = "testuser"
        mock_info.manifest_type = "tool"
        mock_info.declaration = {
            "tools_configuration": [{"name": "tool1"}],
            "models_configuration": [],
            "agent_strategies_configuration": [],
        }

        with patch(
            "tenant.services.plugin_package_service.plugin_package_service"
        ) as mock_svc:
            mock_svc.parse_package_from_bytes.return_value = mock_info
            adapter = LocalPluginAdapter()
            config = {"url": str(tmp_path)}
            data, checksum = await adapter.download_plugin(config, "testuser/test-plugin")

        assert data == zip_data
        assert checksum == hashlib.sha256(zip_data).hexdigest()

    @pytest.mark.asyncio
    async def test_download_plugin_not_found(self, tmp_path: Path):
        """验证下载不存在的插件抛出 ValueError"""
        adapter = LocalPluginAdapter()
        config = {"url": str(tmp_path)}
        with pytest.raises(ValueError, match="Plugin not found"):
            await adapter.download_plugin(config, "nonexistent/plugin")

    @pytest.mark.asyncio
    async def test_check_updates_returns_empty(self, tmp_path: Path):
        """验证本地 Plugin 不支持更新检查，返回空列表"""
        adapter = LocalPluginAdapter()
        config = {"url": str(tmp_path)}
        updates = await adapter.check_updates(config, [{"plugin_id": "test/plugin", "current_version": "1.0.0"}])
        assert updates == []

    def test_determine_plugin_type_model(self):
        """验证从 declaration 推导 model 类型"""
        adapter = LocalPluginAdapter()
        declaration = {
            "models_configuration": [{"name": "qwen"}],
            "tools_configuration": [],
            "agent_strategies_configuration": [],
        }
        assert adapter._determine_plugin_type(declaration) == "model"

    def test_determine_plugin_type_tool(self):
        """验证从 declaration 推导 tool 类型"""
        adapter = LocalPluginAdapter()
        declaration = {
            "models_configuration": [],
            "tools_configuration": [{"name": "search"}],
            "agent_strategies_configuration": [],
        }
        assert adapter._determine_plugin_type(declaration) == "tool"

    def test_determine_plugin_type_agent(self):
        """验证从 declaration 推导 agent 类型"""
        adapter = LocalPluginAdapter()
        declaration = {
            "models_configuration": [],
            "tools_configuration": [],
            "agent_strategies_configuration": [{"name": "react"}],
        }
        assert adapter._determine_plugin_type(declaration) == "agent"

    def test_determine_plugin_type_default_tool(self):
        """验证空 declaration 默认为 tool 类型"""
        adapter = LocalPluginAdapter()
        assert adapter._determine_plugin_type({}) == "tool"
