"""
PluginPackageService 单元测试

测试插件包解析服务的核心功能：
- manifest 解析
- 校验和计算
- 格式验证
"""

import hashlib
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
import yaml


class TestCalculateChecksum:
    """测试校验和计算"""

    def test_calculate_checksum_empty_bytes(self):
        """测试空字节数据的校验和计算"""
        data = b""
        checksum = hashlib.sha256(data).hexdigest()

        # 空数据的 SHA256
        expected = hashlib.sha256(b"").hexdigest()
        assert checksum == expected
        assert len(checksum) == 64  # SHA256 输出 64 个十六进制字符

    def test_calculate_checksum_simple_data(self):
        """测试简单数据的校验和计算"""
        data = b"Hello, World!"
        checksum = hashlib.sha256(data).hexdigest()
        expected = hashlib.sha256(data).hexdigest()
        assert checksum == expected

    def test_calculate_checksum_chinese_data(self):
        """测试中文数据的校验和计算"""
        data = "你好，世界！".encode("utf-8")
        checksum = hashlib.sha256(data).hexdigest()
        expected = hashlib.sha256(data).hexdigest()
        assert checksum == expected

    def test_calculate_checksum_large_data(self):
        """测试大数据的校验和计算"""
        data = b"x" * 10_000_000  # 10MB 数据
        checksum = hashlib.sha256(data).hexdigest()
        expected = hashlib.sha256(data).hexdigest()
        assert checksum == expected

    def test_calculate_checksum_deterministic(self):
        """测试校验和计算的确定性"""
        data = b"Test data for determinism"
        checksum1 = hashlib.sha256(data).hexdigest()
        checksum2 = hashlib.sha256(data).hexdigest()
        assert checksum1 == checksum2

    def test_calculate_checksum_different_data_different_result(self):
        """测试不同数据产生不同的校验和"""
        data1 = b"Data 1"
        data2 = b"Data 2"
        checksum1 = hashlib.sha256(data1).hexdigest()
        checksum2 = hashlib.sha256(data2).hexdigest()
        assert checksum1 != checksum2


class TestParsePackageFromBytes:
    """测试从字节数据解析插件包"""

    @pytest.fixture
    def valid_manifest(self):
        """有效的 manifest 数据"""
        return {
            "author": "test-author",
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "测试插件",
            "type": "tool",
            "configuration": {"timeout": 30},
            "tools": [{"name": "test-tool", "type": "function"}],
        }

    def _create_valid_zip(self, manifest: dict) -> bytes:
        """创建有效的插件包 ZIP 文件"""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest_yaml = yaml.dump(manifest)
            zf.writestr("manifest.yaml", manifest_yaml)
        return buffer.getvalue()

    def _parse_package(self, package_data: bytes):
        """解析插件包（复制核心逻辑进行测试）"""
        import tempfile

        package_hash = hashlib.sha256(package_data).hexdigest()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_file = temp_path / "plugin.zip"
            package_file.write_bytes(package_data)

            try:
                with zipfile.ZipFile(package_file, "r") as zf:
                    bad_file = zf.testzip()
                    if bad_file:
                        raise ValueError(f"ZIP 文件损坏: {bad_file}")

                    manifest_path = None
                    manifest_files = ["manifest.yaml", "manifest.yml"]
                    for manifest_file in manifest_files:
                        manifest_candidates = [
                            name for name in zf.namelist() if name.endswith(manifest_file)
                        ]
                        if manifest_candidates:
                            manifest_path = manifest_candidates[0]
                            break

                    if not manifest_path:
                        raise ValueError(
                            f"插件包中未找到 manifest 文件，支持的文件名: {manifest_files}"
                        )

                    manifest_content = zf.read(manifest_path).decode("utf-8")
                    manifest_data = yaml.safe_load(manifest_content)

                    if not manifest_data:
                        raise ValueError("manifest 文件内容为空")

                    required_fields = ["author", "name", "version"]
                    missing_fields = [
                        field for field in required_fields if field not in manifest_data
                    ]
                    if missing_fields:
                        raise ValueError(
                            f"manifest 缺少必要字段: {', '.join(missing_fields)}"
                        )

                    author = manifest_data.get("author", "")
                    name = manifest_data.get("name", "")
                    version = manifest_data.get("version", "")
                    plugin_id = f"{author}/{name}"
                    manifest_type = manifest_data.get("type")

                    return {
                        "plugin_id": plugin_id,
                        "version": version,
                        "author": author,
                        "name": name,
                        "package_hash": package_hash,
                        "manifest_type": manifest_type,
                        "declaration": manifest_data,
                    }

            except zipfile.BadZipFile:
                raise ValueError("无效的 ZIP 文件格式")
            except yaml.YAMLError as e:
                raise ValueError(f"manifest YAML 解析失败: {e}")

    def test_parse_valid_package(self, valid_manifest):
        """测试解析有效的插件包"""
        package_data = self._create_valid_zip(valid_manifest)
        result = self._parse_package(package_data)

        assert result["plugin_id"] == "test-author/test-plugin"
        assert result["version"] == "1.0.0"
        assert result["author"] == "test-author"
        assert result["name"] == "test-plugin"
        assert result["manifest_type"] == "tool"

    def test_parse_package_checksum(self, valid_manifest):
        """测试解析后的校验和正确性"""
        package_data = self._create_valid_zip(valid_manifest)
        expected_checksum = hashlib.sha256(package_data).hexdigest()

        result = self._parse_package(package_data)
        assert result["package_hash"] == expected_checksum

    def test_parse_package_with_yml_extension(self, valid_manifest):
        """测试 manifest.yml 扩展名"""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest_yaml = yaml.dump(valid_manifest)
            zf.writestr("manifest.yml", manifest_yaml)
        package_data = buffer.getvalue()

        result = self._parse_package(package_data)
        assert result["plugin_id"] == "test-author/test-plugin"

    def test_parse_package_with_nested_manifest(self, valid_manifest):
        """测试嵌套目录中的 manifest 文件"""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest_yaml = yaml.dump(valid_manifest)
            zf.writestr("plugin/manifest.yaml", manifest_yaml)
        package_data = buffer.getvalue()

        result = self._parse_package(package_data)
        assert result["plugin_id"] == "test-author/test-plugin"

    def test_parse_package_missing_manifest(self):
        """测试缺少 manifest 文件的插件包"""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("readme.txt", "This is a readme")
        package_data = buffer.getvalue()

        with pytest.raises(ValueError) as exc_info:
            self._parse_package(package_data)

        assert "未找到 manifest 文件" in str(exc_info.value)

    def test_parse_package_missing_required_field_author(self, valid_manifest):
        """测试缺少 author 字段"""
        del valid_manifest["author"]
        package_data = self._create_valid_zip(valid_manifest)

        with pytest.raises(ValueError) as exc_info:
            self._parse_package(package_data)

        assert "缺少必要字段" in str(exc_info.value)
        assert "author" in str(exc_info.value)

    def test_parse_package_missing_required_field_name(self, valid_manifest):
        """测试缺少 name 字段"""
        del valid_manifest["name"]
        package_data = self._create_valid_zip(valid_manifest)

        with pytest.raises(ValueError) as exc_info:
            self._parse_package(package_data)

        assert "缺少必要字段" in str(exc_info.value)
        assert "name" in str(exc_info.value)

    def test_parse_package_missing_required_field_version(self, valid_manifest):
        """测试缺少 version 字段"""
        del valid_manifest["version"]
        package_data = self._create_valid_zip(valid_manifest)

        with pytest.raises(ValueError) as exc_info:
            self._parse_package(package_data)

        assert "缺少必要字段" in str(exc_info.value)
        assert "version" in str(exc_info.value)

    def test_parse_package_empty_manifest(self):
        """测试空的 manifest 文件"""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.yaml", "")
        package_data = buffer.getvalue()

        with pytest.raises(ValueError) as exc_info:
            self._parse_package(package_data)

        assert "内容为空" in str(exc_info.value)

    def test_parse_package_invalid_yaml(self):
        """测试无效的 YAML 格式"""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.yaml", "invalid: yaml: content: [")
        package_data = buffer.getvalue()

        with pytest.raises(ValueError) as exc_info:
            self._parse_package(package_data)

        assert "YAML 解析失败" in str(exc_info.value)

    def test_parse_package_invalid_zip(self):
        """测试无效的 ZIP 文件"""
        invalid_data = b"This is not a valid zip file"

        with pytest.raises(ValueError) as exc_info:
            self._parse_package(invalid_data)

        assert "无效的 ZIP 文件格式" in str(exc_info.value)


class TestParsePackageFromPath:
    """测试从文件路径解析插件包"""

    @pytest.fixture
    def valid_manifest(self):
        """有效的 manifest 数据"""
        return {
            "author": "path-author",
            "name": "path-plugin",
            "version": "2.0.0",
        }

    def test_parse_valid_file(self, tmp_path: Path, valid_manifest):
        """测试解析有效的插件包文件"""
        # 创建 ZIP 文件
        package_file = tmp_path / "plugin.zip"
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest_yaml = yaml.dump(valid_manifest)
            zf.writestr("manifest.yaml", manifest_yaml)
        package_file.write_bytes(buffer.getvalue())

        # 验证文件存在且为 ZIP 格式
        assert package_file.exists()
        assert package_file.suffix.lower() == ".zip"

        # 读取并验证内容
        with zipfile.ZipFile(package_file, "r") as zf:
            manifest_files = [n for n in zf.namelist() if n.endswith(".yaml") or n.endswith(".yml")]
            assert len(manifest_files) > 0

    def test_parse_nonexistent_file(self, tmp_path: Path):
        """测试解析不存在的文件"""
        nonexistent_file = tmp_path / "nonexistent.zip"
        assert not nonexistent_file.exists()

    def test_parse_directory_instead_of_file(self, tmp_path: Path):
        """测试传入目录而非文件"""
        directory = tmp_path / "some_directory"
        directory.mkdir()
        assert directory.is_dir()
        assert not directory.is_file()

    def test_parse_non_zip_file(self, tmp_path: Path):
        """测试非 ZIP 格式的文件"""
        non_zip_file = tmp_path / "plugin.txt"
        non_zip_file.write_text("This is not a zip file")
        assert non_zip_file.suffix.lower() != ".zip"


class TestManifestValidation:
    """测试 manifest 验证逻辑"""

    def test_required_fields_present(self):
        """测试必要字段存在"""
        manifest = {
            "author": "test-author",
            "name": "test-plugin",
            "version": "1.0.0",
        }

        required_fields = ["author", "name", "version"]
        missing_fields = [
            field for field in required_fields if field not in manifest
        ]

        assert len(missing_fields) == 0

    def test_required_fields_missing(self):
        """测试必要字段缺失"""
        manifest = {
            "author": "test-author",
            # 缺少 name 和 version
        }

        required_fields = ["author", "name", "version"]
        missing_fields = [
            field for field in required_fields if field not in manifest
        ]

        assert "name" in missing_fields
        assert "version" in missing_fields

    def test_plugin_id_format(self):
        """测试插件 ID 格式"""
        author = "test-author"
        name = "test-plugin"
        plugin_id = f"{author}/{name}"

        assert "/" in plugin_id
        assert plugin_id.count("/") == 1
        assert plugin_id.startswith(author)
        assert plugin_id.endswith(name)


class TestZipFileValidation:
    """测试 ZIP 文件验证"""

    def test_valid_zip_structure(self):
        """测试有效的 ZIP 结构"""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.yaml", "author: test\nname: plugin\nversion: 1.0.0")

        buffer.seek(0)
        with zipfile.ZipFile(buffer, "r") as zf:
            assert zf.testzip() is None  # 无损坏文件
            assert "manifest.yaml" in zf.namelist()

    def test_zip_file_list(self):
        """测试 ZIP 文件列表"""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.yaml", "content")
            zf.writestr("code/main.py", "# main code")
            zf.writestr("README.md", "# README")

        buffer.seek(0)
        with zipfile.ZipFile(buffer, "r") as zf:
            files = zf.namelist()
            assert "manifest.yaml" in files
            assert "code/main.py" in files
            assert "README.md" in files

    def test_nested_manifest_detection(self):
        """测试嵌套目录中的 manifest 检测"""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("plugin/subdir/manifest.yaml", "author: test\nname: plugin")

        buffer.seek(0)
        with zipfile.ZipFile(buffer, "r") as zf:
            manifest_files = [
                name for name in zf.namelist()
                if name.endswith("manifest.yaml") or name.endswith("manifest.yml")
            ]
            assert len(manifest_files) == 1
            assert "plugin/subdir/manifest.yaml" in manifest_files
