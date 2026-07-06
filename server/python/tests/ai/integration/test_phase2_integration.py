# tests/ai/integration/test_phase2_integration.py
"""Phase 2 集成测试"""
import pytest
import asyncio
from ai.controllers.v1.chat.event_types import EventType

@pytest.mark.asyncio
class TestPhase2Integration:
    """Phase 2 集成测试"""

    async def test_feedback_and_stats_flow(self, client):
        """测试反馈和统计完整流程"""
        # 1. 提交反馈
        response = await client.post(
            "/ai/console/v1/metadata/feedback",
            json={
                "message_id": "msg-001",
                "rating": 2,
                "feedback": "很有帮助",
            }
        )
        assert response.status_code == 200

        # 2. 查询统计
        response = await client.get("/ai/console/v1/metadata/usage-stats")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_messages"] >= 1

    async def test_chunked_upload_flow(self, client):
        """测试分片上传完整流程"""
        file_id = "test-integration-file"
        total_chunks = 3

        # 1. 上传所有分片
        for i in range(total_chunks):
            response = await client.post(
                "/ai/console/v1/files/upload-chunk",
                data={
                    "file_id": file_id,
                    "chunk_index": str(i),
                    "total_chunks": str(total_chunks),
                },
                files={"file": (f"chunk{i}.bin", b"test", "application/octet-stream")},
            )
            assert response.status_code == 200

        # 2. 验证上传状态
        response = await client.get(
            f"/ai/console/v1/files/upload-state/{file_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["uploadedChunks"]) == total_chunks
