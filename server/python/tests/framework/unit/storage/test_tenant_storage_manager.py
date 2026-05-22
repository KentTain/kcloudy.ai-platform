"""
TenantStorageManager 单元测试
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from framework.storage.tenant_storage_manager import (
    TenantStorageManager,
    get_storage_manager,
    init_storage_manager,
)
from framework.tenant.protocols import TenantStorageConfig
from framework.tenant.enums import StorageType


class TestTenantStorageManager:
    """TenantStorageManager 测试"""

    def test_manager_creation(self):
        """创建存储管理器"""
        mock_storage = MagicMock()
        manager = TenantStorageManager(mock_storage, "default-bucket")

        assert manager._default_storage is mock_storage
        assert manager._default_bucket == "default-bucket"

    def test_register_bucket(self):
        """注册租户存储桶"""
        mock_storage = MagicMock()
        manager = TenantStorageManager(mock_storage, "default-bucket")

        manager.register_bucket("tenant-001", "tenant-001-bucket")

        assert manager._bucket_map["tenant-001"] == "tenant-001-bucket"

    def test_unregister_bucket(self):
        """注销租户存储桶"""
        mock_storage = MagicMock()
        manager = TenantStorageManager(mock_storage, "default-bucket")
        manager.register_bucket("tenant-001", "tenant-001-bucket")

        manager.unregister_bucket("tenant-001")

        assert "tenant-001" not in manager._bucket_map

    def test_get_bucket_with_config(self):
        """获取租户存储桶 - 有配置"""
        mock_storage = MagicMock()
        manager = TenantStorageManager(mock_storage, "default-bucket")

        config = TenantStorageConfig(bucket="custom-bucket")
        bucket = manager.get_bucket("tenant-001", config)

        assert bucket == "custom-bucket"

    def test_get_bucket_from_map(self):
        """获取租户存储桶 - 从注册表"""
        mock_storage = MagicMock()
        manager = TenantStorageManager(mock_storage, "default-bucket")
        manager.register_bucket("tenant-001", "tenant-001-bucket")

        bucket = manager.get_bucket("tenant-001")

        assert bucket == "tenant-001-bucket"

    def test_get_bucket_default(self):
        """获取默认存储桶"""
        mock_storage = MagicMock()
        manager = TenantStorageManager(mock_storage, "default-bucket")

        bucket = manager.get_bucket(None, None)

        assert bucket == "default-bucket"

    def test_build_path_with_config_bucket(self):
        """构建路径 - 有独立存储桶"""
        mock_storage = MagicMock()
        manager = TenantStorageManager(mock_storage, "default-bucket")
        config = TenantStorageConfig(bucket="custom-bucket")

        path = manager._build_path("avatars/user.jpg", "tenant-001", config)

        assert path == "avatars/user.jpg"

    def test_build_path_default_bucket(self):
        """构建路径 - 使用默认存储桶"""
        mock_storage = MagicMock()
        manager = TenantStorageManager(mock_storage, "default-bucket")

        with patch("framework.storage.tenant_storage_manager.get_tenant_id", return_value="tenant-001"):
            path = manager._build_path("avatars/user.jpg", "tenant-001", None)

        assert path == "tenant-001/avatars/user.jpg"


class TestStorageManagerGlobal:
    """全局存储管理器测试"""

    def test_init_and_get(self):
        """初始化并获取"""
        mock_storage = MagicMock()
        manager = init_storage_manager(mock_storage, "default-bucket")

        assert get_storage_manager() is manager
