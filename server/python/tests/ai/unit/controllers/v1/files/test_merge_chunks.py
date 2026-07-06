# tests/ai/unit/controllers/v1/files/test_merge_chunks.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestMergeChunks:
    async def test_merge_chunks_success(self, client: AsyncClient):
        """测试合并分片成功"""
        # 先上传所有分片
        file_id = "test-merge-123"
        total_chunks = 3

        for i in range(total_chunks):
            await client.post(
                "/ai/console/v1/files/upload-chunk",
                data={
                    "file_id": file_id,
                    "chunk_index": str(i),
                    "total_chunks": str(total_chunks),
                },
                files={"file": (f"chunk{i}.bin", b"test", "application/octet-stream")},
            )

        # 合并分片
        response = await client.post(
            "/ai/console/v1/files/merge-chunks",
            json={
                "file_id": file_id,
                "filename": "test.txt",
                "total_chunks": total_chunks,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "url" in data["data"]

    async def test_merge_chunks_incomplete(self, client: AsyncClient):
        """测试分片不完整"""
        response = await client.post(
            "/ai/console/v1/files/merge-chunks",
            json={
                "file_id": "incomplete-file",
                "filename": "test.txt",
                "total_chunks": 5,
            }
        )

        assert response.status_code == 400
