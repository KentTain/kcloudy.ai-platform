"""文件上传 Schema 测试"""

import pytest

from ai.schemas.file import FileUploadResponse


class TestFileUploadSchema:
    """文件上传 Schema 测试"""

    def test_file_upload_response_creation(self):
        """测试文件上传响应 Schema 创建"""
        response = FileUploadResponse(
            url="https://minio.example.com/test.txt",
            media_type="text/plain",
            filename="test.txt",
            size=100,
        )

        assert response.url == "https://minio.example.com/test.txt"
        assert response.media_type == "text/plain"
        assert response.filename == "test.txt"
        assert response.size == 100

    def test_file_upload_response_serialization(self):
        """测试文件上传响应序列化"""
        response = FileUploadResponse(
            url="https://minio.example.com/doc.pdf",
            media_type="application/pdf",
            filename="doc.pdf",
            size=1048576,
        )

        data = response.model_dump()
        assert "url" in data
        assert "media_type" in data
        assert "filename" in data
        assert "size" in data
        assert data["url"] == "https://minio.example.com/doc.pdf"
        assert data["media_type"] == "application/pdf"
        assert data["filename"] == "doc.pdf"
        assert data["size"] == 1048576

    def test_file_upload_response_with_large_file(self):
        """测试大文件上传响应"""
        # 1GB 文件
        large_size = 1024 * 1024 * 1024
        response = FileUploadResponse(
            url="https://minio.example.com/large.zip",
            media_type="application/zip",
            filename="large.zip",
            size=large_size,
        )

        assert response.size == large_size

    def test_file_upload_response_with_special_filename(self):
        """测试特殊文件名"""
        response = FileUploadResponse(
            url="https://minio.example.com/path/file%20name.pdf",
            media_type="application/pdf",
            filename="file name.pdf",
            size=1024,
        )

        assert response.filename == "file name.pdf"
