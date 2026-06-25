"""
Tenant 单元测试配置

提供 Tenant 单元测试的 fixtures。
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# 在导入 tenant 模块之前 mock settings
mock_settings = MagicMock()
mock_settings.oss = MagicMock()
mock_settings.oss.default_type = "minio"
mock_settings.oss.bucket = "test-bucket"
mock_settings.oss.minio = MagicMock()
mock_settings.oss.minio.endpoint = "localhost:9000"
mock_settings.oss.minio.access_key = "test-key"
mock_settings.oss.minio.secret_key = "test-secret"
mock_settings.oss.minio.secure = False
mock_settings.plugin = MagicMock()
mock_settings.plugin.storage_bucket = "plugins"
mock_settings.plugin.install_task_timeout_seconds = 1800

# Patch settings before importing tenant modules
sys.modules["framework.configs"].settings = lambda: mock_settings


@pytest_asyncio.fixture
def session():
    """模拟数据库会话"""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.scalar_one_or_none = AsyncMock()
    mock_session.scalars = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.delete = AsyncMock()
    return mock_session


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
