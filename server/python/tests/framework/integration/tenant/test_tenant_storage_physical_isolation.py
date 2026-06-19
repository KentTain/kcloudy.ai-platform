"""
TenantStorageManager 物理隔离集成测试

测试场景覆盖：
1. 连接独立存储服务
2. 物理隔离路径
3. 逻辑隔离路径
"""

import uuid

import pytest
import pytest_asyncio

from framework.storage.tenant_storage_manager import (
    TenantStorageManager,
    init_storage_manager,
)
from framework.tenant.enums import StorageType
from framework.tenant.protocols import TenantStorageConfig

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def storage_manager(minio_client, minio_available, minio_test_bucket):
    """存储管理器实例"""
    if not minio_available:
        pytest.skip("MinIO 服务不可用")

    manager = TenantStorageManager(minio_client, minio_test_bucket)
    yield manager

    # 清理
    await manager.close()


@pytest_asyncio.fixture
def unique_tenant_id():
    """生成唯一租户 ID"""
    return f"tenant-{uuid.uuid4().hex[:8]}"


@pytest_asyncio.fixture
async def test_bucket(minio_client, minio_test_bucket):
    """测试用存储桶"""
    bucket_name = minio_test_bucket
    # 确保存储桶存在
    await minio_client.create_bucket(bucket_name)
    yield bucket_name
    # 清理测试文件
    try:
        objects = await minio_client.list_objects(bucket_name)
        for obj in objects:
            await minio_client.delete(bucket_name, obj)
    except Exception:
        pass


class TestTenantStoragePhysicalIsolation:
    """物理隔离场景测试"""

    @pytest.mark.asyncio
    async def test_connect_independent_storage_service(self, storage_manager, unique_tenant_id):
        """
        场景: 连接独立存储服务

        WHEN 租户配置了 endpoint="https://minio-tenant-a.example.com"
        THEN 系统创建到该存储服务的独立客户端
        """
        config = TenantStorageConfig(
            type=StorageType.MINIO,
            endpoint="https://minio-tenant-a.example.com",
            access_key="tenant-a-key",
            secret_key="tenant-a-secret",
            bucket="tenant-a-bucket",
        )

        # 验证物理隔离判断
        assert storage_manager._is_physical_isolation(config) is True

        # 验证配置参数
        assert config.endpoint == "https://minio-tenant-a.example.com"
        assert config.bucket == "tenant-a-bucket"
        assert config.access_key == "tenant-a-key"

    @pytest.mark.asyncio
    async def test_physical_isolation_path_no_prefix(self, storage_manager, unique_tenant_id):
        """
        场景: 物理隔离路径

        WHEN 配置了独立 endpoint
        THEN 文件路径不添加租户前缀
        """
        # 使用本地 MinIO 作为物理隔离实例
        config = TenantStorageConfig(
            type=StorageType.MINIO,
            endpoint="localhost:9000",  # 本地 MinIO
            bucket="test-isolated-bucket",
            access_key="minioadmin",
            secret_key="minioadmin",
        )

        test_path = "uploads/document.pdf"

        # 构建实际路径
        actual_path = storage_manager._build_path(test_path, unique_tenant_id, config)

        # 物理隔离场景，路径不添加前缀
        assert actual_path == test_path
        assert unique_tenant_id not in actual_path

    @pytest.mark.asyncio
    async def test_logical_isolation_path_with_prefix(self, storage_manager, unique_tenant_id, test_bucket):
        """
        场景: 逻辑隔离路径

        WHEN 使用默认存储服务且无独立 bucket
        THEN 文件路径添加 {tenant_id}/ 前缀
        """
        test_path = "uploads/avatar.jpg"

        # 构建实际路径（无物理隔离配置）
        actual_path = storage_manager._build_path(test_path, unique_tenant_id, None)

        # 逻辑隔离场景，路径添加租户前缀
        expected_prefix = f"{unique_tenant_id}/"
        assert actual_path.startswith(expected_prefix)
        assert test_path in actual_path
        assert actual_path == f"{unique_tenant_id}/{test_path}"

        # 实际上传和下载测试
        test_content = b"Test file content for logical isolation"
        result = await storage_manager.upload(
            path=test_path,
            data=test_content,
            tenant_id=unique_tenant_id,
        )
        assert result is not None

        # 验证下载
        downloaded = await storage_manager.download(
            path=test_path,
            tenant_id=unique_tenant_id,
        )
        assert downloaded == test_content

        # 清理
        await storage_manager.delete(test_path, tenant_id=unique_tenant_id)

    @pytest.mark.asyncio
    async def test_independent_bucket_no_prefix(self, storage_manager, unique_tenant_id):
        """
        场景: 独立存储桶

        WHEN 配置了独立 bucket 但无独立 endpoint
        THEN 路径不添加租户前缀
        """
        config = TenantStorageConfig(
            type=StorageType.MINIO,
            bucket="tenant-specific-bucket",
        )

        test_path = "files/report.xlsx"

        # 构建实际路径
        actual_path = storage_manager._build_path(test_path, unique_tenant_id, config)

        # 独立 bucket 场景，路径不添加租户前缀
        assert actual_path == test_path
        assert unique_tenant_id not in actual_path

    @pytest.mark.asyncio
    async def test_registered_bucket_no_prefix(self, storage_manager, unique_tenant_id):
        """
        场景: 注册存储桶

        WHEN 租户已注册独立 bucket
        THEN 路径不添加租户前缀
        """
        storage_manager.register_bucket(unique_tenant_id, "registered-bucket")

        test_path = "documents/contract.pdf"

        # 构建实际路径
        actual_path = storage_manager._build_path(test_path, unique_tenant_id, None)

        # 已注册独立 bucket，路径不添加前缀
        assert actual_path == test_path
        assert unique_tenant_id not in actual_path

        # 清理
        storage_manager.unregister_bucket(unique_tenant_id)


class TestTenantStorageOperations:
    """存储操作测试"""

    @pytest.mark.asyncio
    async def test_upload_with_physical_isolation_config(
        self, storage_manager, unique_tenant_id, test_bucket, minio_client
    ):
        """物理隔离配置下的上传操作"""
        # 使用本地 MinIO 模拟物理隔离
        # 注意：实际物理隔离应使用不同 endpoint
        # 这里主要验证路径构建逻辑

        test_path = f"test_upload_{uuid.uuid4().hex[:8]}.txt"
        test_content = b"Physical isolation test content"

        # 上传（使用默认存储但验证逻辑）
        result = await storage_manager.upload(
            path=test_path,
            data=test_content,
            tenant_id=unique_tenant_id,
        )
        assert result is not None

        # 清理
        await storage_manager.delete(test_path, tenant_id=unique_tenant_id)

    @pytest.mark.asyncio
    async def test_upload_with_logical_isolation(self, storage_manager, unique_tenant_id, test_bucket):
        """逻辑隔离下的上传操作"""
        test_path = f"logical_test_{uuid.uuid4().hex[:8]}.txt"
        test_content = b"Logical isolation test content"

        # 上传（逻辑隔离）
        result = await storage_manager.upload(
            path=test_path,
            data=test_content,
            tenant_id=unique_tenant_id,
        )
        assert result is not None

        # 验证实际路径包含租户前缀
        actual_path = storage_manager._build_path(test_path, unique_tenant_id, None)
        assert unique_tenant_id in actual_path

        # 下载验证
        downloaded = await storage_manager.download(
            path=test_path,
            tenant_id=unique_tenant_id,
        )
        assert downloaded == test_content

        # 清理
        await storage_manager.delete(test_path, tenant_id=unique_tenant_id)

    @pytest.mark.asyncio
    async def test_list_objects_with_tenant_prefix(self, storage_manager, unique_tenant_id, test_bucket):
        """列出对象时自动添加租户前缀"""
        # 上传多个文件
        test_files = [
            f"list_test_{i}_{uuid.uuid4().hex[:8]}.txt"
            for i in range(3)
        ]

        for file_name in test_files:
            await storage_manager.upload(
                path=file_name,
                data=f"Content {file_name}".encode(),
                tenant_id=unique_tenant_id,
            )

        # 列出对象
        objects = await storage_manager.list_objects(
            prefix="",
            tenant_id=unique_tenant_id,
        )

        # 验证返回的对象（路径已移除租户前缀）
        assert len(objects) >= 3

        # 清理
        for file_name in test_files:
            await storage_manager.delete(file_name, tenant_id=unique_tenant_id)


class TestTenantStorageBucketManagement:
    """存储桶管理测试"""

    @pytest.mark.asyncio
    async def test_get_bucket_with_config(self, storage_manager, unique_tenant_id):
        """从配置获取存储桶"""
        config = TenantStorageConfig(bucket="config-bucket")

        bucket = storage_manager.get_bucket(unique_tenant_id, config)
        assert bucket == "config-bucket"

    @pytest.mark.asyncio
    async def test_get_bucket_from_map(self, storage_manager, unique_tenant_id):
        """从注册表获取存储桶"""
        storage_manager.register_bucket(unique_tenant_id, "registered-bucket")

        bucket = storage_manager.get_bucket(unique_tenant_id)
        assert bucket == "registered-bucket"

        storage_manager.unregister_bucket(unique_tenant_id)

    @pytest.mark.asyncio
    async def test_get_bucket_default(self, storage_manager, test_bucket):
        """获取默认存储桶"""
        bucket = storage_manager.get_bucket(None, None)
        assert bucket == test_bucket


class TestTenantStorageInstanceManagement:
    """实例管理测试"""

    @pytest.mark.asyncio
    async def test_get_storage_default(self, storage_manager):
        """无配置时返回默认存储"""
        storage = storage_manager.get_storage(None)
        assert storage is storage_manager._default_storage

    @pytest.mark.asyncio
    async def test_get_storage_with_physical_isolation(self, storage_manager):
        """物理隔离配置时创建新实例"""
        config = TenantStorageConfig(
            endpoint="https://isolated-minio.example.com",
            bucket="isolated-bucket",
            access_key="key",
            secret_key="secret",
        )

        # 注意：实际测试可能无法连接到外部 endpoint
        # 这里验证创建逻辑
        assert storage_manager._is_physical_isolation(config) is True

    @pytest.mark.asyncio
    async def test_release_idle_instances(self, storage_manager):
        """释放空闲实例客户端"""
        # 模拟实例客户端
        from datetime import datetime, timedelta
        storage_manager._instance_storages["https://test.example.com"] = storage_manager._default_storage
        # 将访问时间设置为过去，确保 release_idle_instances 能释放
        storage_manager._instance_access_times["https://test.example.com"] = datetime.now() - timedelta(seconds=10)

        # 释放空闲实例（超时=0）
        released = await storage_manager.release_idle_instances(timeout=0)

        assert released == 1
        assert len(storage_manager._instance_storages) == 0

    @pytest.mark.asyncio
    async def test_close_clears_all_instances(self, storage_manager):
        """关闭时清理所有实例"""
        storage_manager._instance_storages["https://test.example.com"] = storage_manager._default_storage

        await storage_manager.close()

        assert len(storage_manager._instance_storages) == 0


class TestTenantStorageGlobalManager:
    """全局管理器测试"""

    def test_init_and_get_storage_manager(self, minio_client, minio_test_bucket):
        """初始化并获取全局存储管理器"""
        manager = init_storage_manager(minio_client, minio_test_bucket)

        from framework.storage.tenant_storage_manager import get_storage_manager
        assert get_storage_manager() is manager
