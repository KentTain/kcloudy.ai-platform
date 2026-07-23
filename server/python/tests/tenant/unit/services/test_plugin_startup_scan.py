"""
插件启动扫描服务测试
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from tenant.services.plugin import (
    StartupScanResult,
    scan_plugins_at_startup,
)


class TestStartupScanResult:
    """StartupScanResult 数据结构测试"""

    def test_default_values(self):
        """测试默认值"""
        result = StartupScanResult()
        assert result.total_count == 0
        assert result.success_count == 0
        assert result.skipped_count == 0
        assert result.failed_count == 0
        assert result.errors == []

    def test_custom_values(self):
        """测试自定义值"""
        result = StartupScanResult(
            total_count=10,
            success_count=5,
            skipped_count=3,
            failed_count=2,
            errors=["error1", "error2"],
        )
        assert result.total_count == 10
        assert result.success_count == 5
        assert result.skipped_count == 3
        assert result.failed_count == 2
        assert result.errors == ["error1", "error2"]


class TestScanPluginsAtStartup:
    """scan_plugins_at_startup 函数测试"""

    @pytest.fixture
    def mock_session(self):
        """创建模拟数据库会话"""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_directory_not_exists(self, mock_session, tmp_path):
        """测试目录不存在的情况"""
        non_existent = tmp_path / "non_existent"
        result = await scan_plugins_at_startup(mock_session, str(non_existent))

        assert result.total_count == 0
        assert result.success_count == 0

    @pytest.mark.asyncio
    async def test_directory_is_file(self, mock_session, tmp_path):
        """测试路径是文件而非目录的情况"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        result = await scan_plugins_at_startup(mock_session, str(file_path))

        assert result.total_count == 0
        assert result.success_count == 0

    @pytest.mark.asyncio
    async def test_empty_directory(self, mock_session, tmp_path):
        """测试空目录"""
        result = await scan_plugins_at_startup(mock_session, str(tmp_path))

        assert result.total_count == 0
        assert result.success_count == 0

    @pytest.mark.asyncio
    async def test_invalid_zip_file(self, mock_session, tmp_path):
        """测试无效的 ZIP 文件"""
        # 创建一个无效的 .zip 文件
        invalid_zip = tmp_path / "invalid.zip"
        invalid_zip.write_text("not a zip file")

        with patch(
            "tenant.services.plugin_startup_scan_service.plugin_definition_service"
        ) as mock_service:
            result = await scan_plugins_at_startup(mock_session, str(tmp_path))

        assert result.total_count == 1
        assert result.success_count == 0
        assert result.failed_count == 1
        assert len(result.errors) == 1
