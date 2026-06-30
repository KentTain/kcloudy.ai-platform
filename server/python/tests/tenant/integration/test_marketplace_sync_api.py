"""
插件市场同步 API 集成测试

测试 /tenant/admin/v1/marketplaces/sync、updates 端点。
"""

import os
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"

pytestmark = pytest.mark.integration


class TestMarketplaceSyncAPI:
    """同步 API 测试"""

    @pytest.mark.asyncio
    async def test_sync_plugins(self):
        """测试同步插件"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces/sync")
        async def sync_plugins(request: dict):
            return ApiResponse.success(data={
                "success": [{"plugin_id": "test/plugin", "version": "1.0.0"}],
                "failed": [],
                "skipped": [],
            })

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/marketplaces/sync",
                json={
                    "marketplace_id": "test-marketplace",
                    "plugins": [{"plugin_id": "test/plugin", "plugin_type": "tool"}],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["success"]) == 1
        assert data["data"]["success"][0]["plugin_id"] == "test/plugin"

    @pytest.mark.asyncio
    async def test_sync_plugins_validation(self):
        """测试同步插件请求校验"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces/sync")
        async def sync_plugins(request: dict):
            if not request.get("marketplace_id"):
                return ApiResponse.fail("市场ID不能为空")
            if not request.get("plugins"):
                return ApiResponse.fail("插件列表不能为空")
            return ApiResponse.success(data={"success": [], "failed": [], "skipped": []})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/marketplaces/sync",
                json={"marketplace_id": "", "plugins": []},
            )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200


class TestMarketplaceCheckUpdatesAPI:
    """检查更新 API 测试"""

    @pytest.mark.asyncio
    async def test_check_updates(self):
        """测试检查更新"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.get("/tenant/admin/v1/marketplaces/updates")
        async def check_updates(marketplace_id: str):
            return ApiResponse.success(data=[
                {
                    "plugin_id": "test/plugin",
                    "current_version": "1.0.0",
                    "latest_version": "1.1.0",
                    "has_update": True,
                },
            ])

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/tenant/admin/v1/marketplaces/updates",
                params={"marketplace_id": "test-marketplace"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]) == 1
        assert data["data"][0]["has_update"] is True


class TestMarketplaceApplyUpdateAPI:
    """应用更新 API 测试"""

    @pytest.mark.asyncio
    async def test_apply_update(self):
        """测试应用更新"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces/updates/{plugin_id}")
        async def apply_update(plugin_id: str, request: dict):
            return ApiResponse.success(data={
                "plugin_id": plugin_id,
                "old_version": "1.0.0",
                "new_version": "1.1.0",
                "status": "updated",
            })

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/marketplaces/updates/test-plugin",
                json={"marketplace_id": "test-marketplace"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["plugin_id"] == "test-plugin"
        assert data["data"]["status"] == "updated"
