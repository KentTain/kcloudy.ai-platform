"""
插件包解析导入测试

测试插件包的解析和校验功能，包括：
- 正常插件包的解析和元数据提取
- 无效插件包的错误处理

运行方式：
    uv run pytest -m e2e tests/ai/e2e/test_plugin_parse.py -v
"""

import zipfile
from pathlib import Path

import pytest

from tenant.services.plugin import (
    PluginPackageService,
    PluginPackageInfo,
)


class TestPluginPackageParse:
    """插件包解析测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_parse_tongyi_plugin_package(
        self, plugin_package_path: callable
    ) -> None:
        """
        测试解析 tongyi 插件包并验证元数据

        场景：解析 tongyi 插件包
        - 上传 tongyi 插件包到系统
        - 系统成功解析 manifest.yaml
        - 提取正确的插件元数据（author、name、version、type）
        - 插件 ID 格式为 `langgenius/tongyi`
        """
        # 获取 tongyi 插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")

        # 解析插件包
        result: PluginPackageInfo = PluginPackageService.parse_package_from_path(
            tongyi_path
        )

        # 验证解析结果
        assert result is not None, "解析结果不应为空"
        assert isinstance(result, PluginPackageInfo), "返回类型应为 PluginPackageInfo"

        # 验证插件 ID 格式
        assert result.plugin_id == "langgenius/tongyi", (
            f"插件 ID 应为 'langgenius/tongyi'，实际为 '{result.plugin_id}'"
        )

        # 验证元数据
        assert result.author == "langgenius", (
            f"作者应为 'langgenius'，实际为 '{result.author}'"
        )
        assert result.name == "tongyi", f"名称应为 'tongyi'，实际为 '{result.name}'"
        assert result.version == "0.2.0", (
            f"版本应为 '0.2.0'，实际为 '{result.version}'"
        )
        assert result.manifest_type == "plugin", (
            f"类型应为 'plugin'，实际为 '{result.manifest_type}'"
        )

        # 验证校验和存在
        assert result.package_hash, "包校验和不应为空"
        assert len(result.package_hash) == 64, "SHA256 校验和应为 64 字符"

        # 验证声明内容
        assert result.declaration is not None, "声明内容不应为空"
        assert "_manifest" in result.declaration, "声明应包含 _manifest 字段"

        # 验证图标字段存在
        assert "icon" in result.declaration.get("_manifest", {}), (
            "声明应包含 icon 字段"
        )
        icon_path = result.declaration["_manifest"]["icon"]
        assert icon_path, "图标路径不应为空"
        assert icon_path == "icon_s_en.png", (
            f"图标路径应为 'icon_s_en.png'，实际为 '{icon_path}'"
        )

        # 验证图标文件在插件包中存在
        with zipfile.ZipFile(tongyi_path, "r") as zf:
            asset_icon_path = f"_assets/{icon_path}"
            assert asset_icon_path in zf.namelist(), (
                f"图标文件 '{asset_icon_path}' 应在插件包的 _assets 目录中存在"
            )

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_parse_gpustack_plugin_package(
        self, plugin_package_path: callable
    ) -> None:
        """
        测试解析 gpustack 插件包并验证元数据

        场景：解析 gpustack 插件包
        - 上传 gpustack 插件包到系统
        - 系统成功解析 manifest.yaml
        - 提取正确的插件元数据
        """
        # 获取 gpustack 插件包路径
        gpustack_path: Path = plugin_package_path("gpustack")

        # 解析插件包
        result: PluginPackageInfo = PluginPackageService.parse_package_from_path(
            gpustack_path
        )

        # 验证解析结果
        assert result is not None, "解析结果不应为空"
        assert isinstance(result, PluginPackageInfo), "返回类型应为 PluginPackageInfo"

        # 验证插件 ID 格式
        assert result.plugin_id == "langgenius/gpustack", (
            f"插件 ID 应为 'langgenius/gpustack'，实际为 '{result.plugin_id}'"
        )

        # 验证元数据
        assert result.author == "langgenius", (
            f"作者应为 'langgenius'，实际为 '{result.author}'"
        )
        assert result.name == "gpustack", (
            f"名称应为 'gpustack'，实际为 '{result.name}'"
        )
        assert result.version == "0.0.15", (
            f"版本应为 '0.0.15'，实际为 '{result.version}'"
        )
        assert result.manifest_type == "plugin", (
            f"类型应为 'plugin'，实际为 '{result.manifest_type}'"
        )

        # 验证校验和存在
        assert result.package_hash, "包校验和不应为空"
        assert len(result.package_hash) == 64, "SHA256 校验和应为 64 字符"

        # 验证声明内容
        assert result.declaration is not None, "声明内容不应为空"
        assert "_manifest" in result.declaration, "声明应包含 _manifest 字段"

        # 验证图标字段存在
        assert "icon" in result.declaration.get("_manifest", {}), (
            "声明应包含 icon 字段"
        )
        icon_path = result.declaration["_manifest"]["icon"]
        assert icon_path, "图标路径不应为空"
        assert icon_path == "icon_s_en.png", (
            f"图标路径应为 'icon_s_en.png'，实际为 '{icon_path}'"
        )

        # 验证图标文件在插件包中存在
        with zipfile.ZipFile(gpustack_path, "r") as zf:
            asset_icon_path = f"_assets/{icon_path}"
            assert asset_icon_path in zf.namelist(), (
                f"图标文件 '{asset_icon_path}' 应在插件包的 _assets 目录中存在"
            )

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_parse_invalid_plugin_package_missing_manifest(
        self, plugin_package_path: callable, tmp_path: Path
    ) -> None:
        """
        测试解析缺少 manifest 的无效插件包

        场景：解析缺少 manifest.yaml 的无效插件包
        - 上传缺少 manifest.yaml 的插件包
        - 系统拒绝安装并返回错误信息
        - 错误信息包含"未找到 manifest 文件"
        """
        # 创建一个缺少 manifest 的无效插件包
        invalid_package_path = tmp_path / "invalid_plugin.zip"

        with zipfile.ZipFile(invalid_package_path, "w") as zf:
            # 添加一些文件，但不包含 manifest.yaml
            zf.writestr("README.md", "# Invalid Plugin\n\nThis plugin has no manifest.")
            zf.writestr("main.py", "# Empty main file")

        # 尝试解析无效插件包
        with pytest.raises(ValueError) as exc_info:
            PluginPackageService.parse_package_from_path(invalid_package_path)

        # 验证错误信息
        error_message = str(exc_info.value)
        assert "manifest" in error_message.lower(), (
            f"错误信息应包含 'manifest'，实际为: {error_message}"
        )

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_parse_invalid_plugin_package_missing_required_fields(
        self, tmp_path: Path
    ) -> None:
        """
        测试解析缺少必要字段的无效插件包

        场景：manifest.yaml 存在但缺少必要字段（author、name、version）
        """
        # 创建一个缺少必要字段的插件包
        invalid_package_path = tmp_path / "missing_fields_plugin.zip"

        # 创建缺少 author 字段的 manifest
        invalid_manifest = """
name: test_plugin
version: 1.0.0
type: plugin
"""

        with zipfile.ZipFile(invalid_package_path, "w") as zf:
            zf.writestr("manifest.yaml", invalid_manifest)

        # 尝试解析无效插件包
        with pytest.raises(ValueError) as exc_info:
            PluginPackageService.parse_package_from_path(invalid_package_path)

        # 验证错误信息
        error_message = str(exc_info.value)
        assert "缺少必要字段" in error_message or "author" in error_message.lower(), (
            f"错误信息应提及缺少必要字段，实际为: {error_message}"
        )

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_parse_plugin_package_from_bytes(
        self, plugin_package_path: callable
    ) -> None:
        """
        测试从字节数据解析插件包

        验证 parse_package_from_bytes 方法正常工作
        """
        # 获取 tongyi 插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")

        # 读取为字节数据
        package_data = tongyi_path.read_bytes()

        # 解析插件包
        result: PluginPackageInfo = PluginPackageService.parse_package_from_bytes(
            package_data
        )

        # 验证解析结果
        assert result is not None, "解析结果不应为空"
        assert result.plugin_id == "langgenius/tongyi", (
            f"插件 ID 应为 'langgenius/tongyi'，实际为 '{result.plugin_id}'"
        )

        # 验证校验和是通过传入数据计算的
        expected_hash = PluginPackageService.calculate_checksum(package_data)
        assert result.package_hash == expected_hash, "校验和应与输入数据匹配"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_parse_nonexistent_plugin_package(self) -> None:
        """
        测试解析不存在的插件包

        验证对不存在文件的处理
        """
        nonexistent_path = Path("/nonexistent/plugin.zip")

        with pytest.raises(FileNotFoundError) as exc_info:
            PluginPackageService.parse_package_from_path(nonexistent_path)

        assert "不存在" in str(exc_info.value) or "not found" in str(exc_info.value).lower()
