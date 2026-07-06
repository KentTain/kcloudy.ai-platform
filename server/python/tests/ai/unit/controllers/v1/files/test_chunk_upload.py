# tests/ai/unit/controllers/v1/files/test_chunk_upload.py
import pytest
from httpx import AsyncClient
from io import BytesIO

@pytest.mark.asyncio
class TestChunkUpload:
    async def test_upload_chunk_success(self, client: AsyncClient):
        """测试上传分片成功"""
        file_content = b"test chunk content"
        file_obj = BytesIO(file_content)

        response = await client.post(
            "/ai/console/v1/files/upload-chunk",
            data={
                "file_id": "test-file-123",
                "chunk_index": "0",
                "total_chunks": "5",
            },
            files={"file": ("chunk.bin", file_obj, "application/octet-stream")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["chunkIndex"] == 0

    async def test_get_upload_state(self, client: AsyncClient):
        """测试查询上传状态"""
        # 先上传一个分片
        await client.post(
            "/ai/console/v1/files/upload-chunk",
            data={
                "file_id": "test-file-456",
                "chunk_index": "1",
                "total_chunks": "5",
            },
            files={"file": ("chunk.bin", BytesIO(b"test"), "application/octet-stream")},
        )

        # 查询状态
        response = await client.get(
            "/ai/console/v1/files/upload-state/test-file-456"
        )

        assert response.status_code == 200
        data = response.json()
        assert 1 in data["data"]["uploadedChunks"]
