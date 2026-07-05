# tests/ai/unit/controllers/v1/metadata/test_stats.py
import pytest
from httpx import AsyncClient
from datetime import date

@pytest.mark.asyncio
class TestStats:
    async def test_get_usage_stats(self, client: AsyncClient):
        """测试获取使用统计"""
        # 先创建一些测试数据
        await client.post(
            "/ai/console/v1/metadata/feedback",
            json={"message_id": "msg-001", "rating": 2}
        )

        response = await client.get(
            "/ai/console/v1/metadata/usage-stats",
            params={
                "start_date": "2026-07-01",
                "end_date": "2026-07-31",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "total_messages" in data["data"]
        assert "total_tokens" in data["data"]
        assert "period" in data["data"]
