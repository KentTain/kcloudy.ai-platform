"""
Tenant 模块测试配置

提供 Tenant 模块的测试 fixtures：
- Mock 插件存储服务
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_plugin_storage_service():
    """模拟插件存储服务"""
    mock_service = MagicMock()
    mock_service.upload_plugin_package = AsyncMock()
    mock_service.delete_plugin_package = AsyncMock(return_value=True)
    mock_service.delete_all_versions = AsyncMock(return_value=2)
    mock_service.package_exists = AsyncMock(return_value=True)
    mock_service.download_package = AsyncMock(return_value=b"fake package data")
    return mock_service
