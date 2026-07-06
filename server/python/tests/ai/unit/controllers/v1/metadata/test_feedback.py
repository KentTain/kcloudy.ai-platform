# tests/ai/unit/controllers/v1/metadata/test_feedback.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestFeedback:
    async def test_submit_feedback_success(self, client: AsyncClient):
        """测试提交反馈成功"""
        response = await client.post(
            "/ai/console/v1/metadata/feedback",
            json={
                "message_id": "msg-123",
                "rating": 2,
                "feedback": "很有帮助",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["message_id"] == "msg-123"
        assert data["data"]["rating"] == 2

    async def test_submit_feedback_update(self, client: AsyncClient):
        """测试更新反馈"""
        # 第一次提交
        await client.post(
            "/ai/console/v1/metadata/feedback",
            json={"message_id": "msg-456", "rating": 1}
        )

        # 更新反馈
        response = await client.post(
            "/ai/console/v1/metadata/feedback",
            json={
                "message_id": "msg-456",
                "rating": 2,
                "feedback": "重新评价",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["rating"] == 2
