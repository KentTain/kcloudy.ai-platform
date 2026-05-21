"""
MinIO 对象存储集成测试

测试 MinioStorage 与真实 MinIO 服务的交互。
使用 @pytest.mark.integration 标记。
"""

import uuid

import pytest
import pytest_asyncio

from framework.storage.impl.minio import MinioStorage


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def minio_storage(integration_settings, minio_available):
    """MinIO 存储实例"""
    if not minio_available:
        pytest.skip("MinIO 服务不可用")

    return MinioStorage(integration_settings.oss.minio)


@pytest_asyncio.fixture
async def test_bucket(minio_storage, minio_test_bucket):
    """测试用存储桶"""
    bucket_name = minio_test_bucket  # 从 minio_test_bucket fixture 获取名称
    # 确保存储桶存在
    await minio_storage.create_bucket(bucket_name)
    yield bucket_name
    # 清理：删除测试文件
    try:
        objects = await minio_storage.list_objects(bucket_name)
        for obj in objects:
            await minio_storage.delete(bucket_name, obj)
    except Exception:
        pass


class TestMinioStorageUpload:
    """MinIO 文件上传测试"""

    @pytest.mark.asyncio
    async def test_upload_success(self, minio_storage, test_bucket):
        """
        场景：文件上传
        WHEN: 调用 upload 上传文件
        THEN: 文件成功存储并返回访问路径
        """
        file_name = f"test_{uuid.uuid4().hex}.txt"
        file_content = b"Hello, MinIO!"

        result = await minio_storage.upload(
            bucket=test_bucket,
            name=file_name,
            data=file_content,
            content_type="text/plain"
        )

        assert result is not None
        assert test_bucket in result
        assert file_name in result

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="大文件上传可能因网络问题超时，跳过")
    async def test_upload_large_file(self, minio_storage, test_bucket):
        """
        场景：上传大文件
        WHEN: 上传较大的文件
        THEN: 成功上传
        """
        file_name = f"large_{uuid.uuid4().hex}.bin"
        # 1MB 文件
        file_content = b"x" * (1024 * 1024)

        result = await minio_storage.upload(
            bucket=test_bucket,
            name=file_name,
            data=file_content,
            content_type="application/octet-stream"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_upload_with_path(self, minio_storage, test_bucket):
        """
        场景：上传带路径的文件
        WHEN: 上传文件到指定路径
        THEN: 成功上传并保留路径
        """
        file_name = f"subdir/test_{uuid.uuid4().hex}.txt"
        file_content = b"Nested file content"

        result = await minio_storage.upload(
            bucket=test_bucket,
            name=file_name,
            data=file_content,
            content_type="text/plain"
        )

        assert result is not None
        assert "subdir/" in result


class TestMinioStorageDownload:
    """MinIO 文件下载测试"""

    @pytest.mark.asyncio
    async def test_download_success(self, minio_storage, test_bucket):
        """
        场景：文件下载
        WHEN: 下载已上传的文件
        THEN: 返回正确的文件内容
        """
        file_name = f"download_{uuid.uuid4().hex}.txt"
        file_content = b"Download test content"

        # 先上传
        await minio_storage.upload(
            bucket=test_bucket,
            name=file_name,
            data=file_content,
            content_type="text/plain"
        )

        # 再下载
        downloaded = await minio_storage.download(test_bucket, file_name)

        assert downloaded == file_content

    @pytest.mark.asyncio
    async def test_download_nonexistent_file(self, minio_storage, test_bucket):
        """
        场景：下载不存在的文件
        WHEN: 下载不存在的文件
        THEN: 抛出异常
        """
        with pytest.raises(Exception, match=".*"):
            await minio_storage.download(test_bucket, "nonexistent_file.txt")


class TestMinioStorageDelete:
    """MinIO 文件删除测试"""

    @pytest.mark.asyncio
    async def test_delete_success(self, minio_storage, test_bucket):
        """
        场景：文件删除
        WHEN: 删除已上传的文件
        THEN: 文件被成功删除
        """
        file_name = f"delete_{uuid.uuid4().hex}.txt"
        file_content = b"To be deleted"

        # 上传
        await minio_storage.upload(
            bucket=test_bucket,
            name=file_name,
            data=file_content,
            content_type="text/plain"
        )

        # 验证存在
        exists = await minio_storage.exists(test_bucket, file_name)
        assert exists is True

        # 删除
        result = await minio_storage.delete(test_bucket, file_name)
        assert result is True

        # 验证已删除
        exists = await minio_storage.exists(test_bucket, file_name)
        assert exists is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, minio_storage, test_bucket):
        """
        场景：删除不存在的文件
        WHEN: 删除不存在的文件
        THEN: MinIO 客户端不报错即视为成功
        """
        result = await minio_storage.delete(test_bucket, "nonexistent_file.txt")
        # MinIO remove_object 不检查文件是否存在，总是返回 None/True
        assert result in (True, None)


class TestMinioStorageExists:
    """MinIO 文件存在检查测试"""

    @pytest.mark.asyncio
    async def test_exists_true(self, minio_storage, test_bucket):
        """
        场景：文件存在
        WHEN: 检查已上传的文件
        THEN: 返回 True
        """
        file_name = f"exists_{uuid.uuid4().hex}.txt"
        file_content = b"Exists check"

        await minio_storage.upload(
            bucket=test_bucket,
            name=file_name,
            data=file_content,
            content_type="text/plain"
        )

        exists = await minio_storage.exists(test_bucket, file_name)
        assert exists is True

    @pytest.mark.asyncio
    async def test_exists_false(self, minio_storage, test_bucket):
        """
        场景：文件不存在
        WHEN: 检查不存在的文件
        THEN: 返回 False
        """
        exists = await minio_storage.exists(test_bucket, "nonexistent_file.txt")
        assert exists is False


class TestMinioStoragePresignedUrl:
    """MinIO 预签名 URL 测试"""

    @pytest.mark.asyncio
    async def test_get_presigned_url(self, minio_storage, test_bucket):
        """
        场景：获取预签名 URL
        WHEN: 调用 get_presigned_url
        THEN: 返回有效的访问 URL
        """
        file_name = f"presigned_{uuid.uuid4().hex}.txt"
        file_content = b"Presigned URL test"

        await minio_storage.upload(
            bucket=test_bucket,
            name=file_name,
            data=file_content,
            content_type="text/plain"
        )

        url = await minio_storage.get_presigned_url(test_bucket, file_name, expires=3600)

        assert url is not None
        assert isinstance(url, str)
        assert "http" in url

    @pytest.mark.asyncio
    async def test_get_presigned_url_with_custom_expiry(self, minio_storage, test_bucket):
        """
        场景：自定义过期时间
        WHEN: 指定自定义过期时间
        THEN: 成功生成 URL
        """
        file_name = f"presigned_custom_{uuid.uuid4().hex}.txt"
        file_content = b"Custom expiry test"

        await minio_storage.upload(
            bucket=test_bucket,
            name=file_name,
            data=file_content,
            content_type="text/plain"
        )

        url = await minio_storage.get_presigned_url(test_bucket, file_name, expires=7200)

        assert url is not None


class TestMinioStorageBucket:
    """MinIO 存储桶操作测试"""

    @pytest.mark.asyncio
    async def test_bucket_exists_true(self, minio_storage, test_bucket):
        """
        场景：存储桶存在
        WHEN: 检查已创建的存储桶
        THEN: 返回 True
        """
        bucket_name = test_bucket  # 使用 fixture 返回的值
        exists = await minio_storage.bucket_exists(bucket_name)
        assert exists is True

    @pytest.mark.asyncio
    async def test_bucket_exists_false(self, minio_storage):
        """
        场景：存储桶不存在
        WHEN: 检查不存在的存储桶
        THEN: 返回 False
        """
        exists = await minio_storage.bucket_exists("nonexistent-bucket-name-xyz123")
        assert exists is False

    @pytest.mark.asyncio
    async def test_create_bucket_success(self, minio_storage):
        """
        场景：创建存储桶
        WHEN: 创建新存储桶
        THEN: 成功创建
        """
        bucket_name = f"test-{uuid.uuid4().hex[:12]}"

        result = await minio_storage.create_bucket(bucket_name)
        assert result is True

        # 验证存在
        exists = await minio_storage.bucket_exists(bucket_name)
        assert exists is True

    @pytest.mark.asyncio
    async def test_list_objects(self, minio_storage, test_bucket):
        """
        场景：列出对象
        WHEN: 列出存储桶中的对象
        THEN: 返回正确的对象列表
        """
        bucket_name = test_bucket
        # 上传多个文件
        for i in range(3):
            file_name = f"list_{i}_{uuid.uuid4().hex}.txt"
            await minio_storage.upload(
                bucket=bucket_name,
                name=file_name,
                data=f"Content {i}".encode(),
                content_type="text/plain"
            )

        # 列出对象
        objects = await minio_storage.list_objects(bucket_name)

        assert isinstance(objects, list)
        assert len(objects) >= 3
