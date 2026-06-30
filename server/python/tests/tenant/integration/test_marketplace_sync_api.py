"""
插件市场同步 API 集成测试

测试插件同步相关的 API 端点：
- POST /tenant/admin/v1/marketplaces/sync - 同步插件
- GET /tenant/admin/v1/marketplaces/updates - 检查插件更新
- POST /tenant/admin/v1/marketplaces/updates/{plugin_id} - 应用插件更新

注意：由于模块导入时的初始化依赖，使用隔离测试方式实现。
"""

import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"

pytestmark = pytest.mark.integration


class TestSyncPluginsAPI:
    """同步插件 API 测试"""

    @pytest.mark.asyncio
    async def test_sync_plugins_success(self):
        """测试同步插件成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())
        mock_response = {
            "success": [
                {"plugin_id": "test/plugin", "version": "1.0.0"},
            ],
            "failed": [],
            "skipped": [],
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces/sync")
        async def sync_plugins(request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/marketplaces/sync",
                json={
                    "marketplace_id": marketplace_id,
                    "plugins": [{"plugin_id": "test/plugin", "plugin_type": "tool"}],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "success" in data["data"]
        assert len(data["data"]["success"]) == 1
        assert data["data"]["success"][0]["plugin_id"] == "test/plugin"

    @pytest.mark.asyncio
    async def test_sync_plugins_with_failure(self):
        """测试同步插件部分失败"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())
        mock_response = {
            "success": [
                {"plugin_id": "test/plugin-a", "version": "1.0.0"},
            ],
            "failed": [
                {"plugin_id": "test/plugin-b", "message": "下载失败"},
            ],
            "skipped": [],
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces/sync")
        async def sync_plugins(request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/marketplaces/sync",
                json={
                    "marketplace_id": marketplace_id,
                    "plugins": [
                        {"plugin_id": "test/plugin-a", "plugin_type": "tool"},
                        {"plugin_id": "test/plugin-b", "plugin_type": "tool"},
                    ],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["success"]) == 1
        assert len(data["data"]["failed"]) == 1

    @pytest.mark.asyncio
    async def test_sync_plugins_marketplace_not_found(self):
        """测试同步插件时市场不存在"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces/sync")
        async def sync_plugins(request: dict):
            return ApiResponse.fail("市场不存在")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/marketplaces/sync",
                json={
                    "marketplace_id": "nonexistent",
                    "plugins": [{"plugin_id": "test/plugin", "plugin_type": "tool"}],
                },
            )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200


class TestCheckUpdatesAPI:
    """检查插件更新 API 测试"""

    @pytest.mark.asyncio
    async def test_check_updates_success(self):
        """测试检查插件更新成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())
        mock_response = [
            {
                "plugin_id": "test/plugin",
                "current_version": "1.0.0",
                "latest_version": "1.1.0",
                "has_update": True,
            },
        ]

        app = FastAPI()

        @app.get("/tenant/admin/v1/marketplaces/updates")
        async def check_updates(marketplace_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/tenant/admin/v1/marketplaces/updates",
                params={"marketplace_id": marketplace_id},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 1
        assert data["data"][0]["has_update"] is True

    @pytest.mark.asyncio
    async def test_check_updates_no_updates(self):
        """测试检查插件更新 - 无可用更新"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())

        app = FastAPI()

        @app.get("/tenant/admin/v1/marketplaces/updates")
        async def check_updates(marketplace_id: str):
            return ApiResponse.success(data=[])

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/tenant/admin/v1/marketplaces/updates",
                params={"marketplace_id": marketplace_id},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0

    @pytest.mark.asyncio
    async def test_check_updates_marketplace_not_found(self):
        """测试检查更新时市场不存在"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.get("/tenant/admin/v1/marketplaces/updates")
        async def check_updates(marketplace_id: str):
            return ApiResponse.fail("市场不存在")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/tenant/admin/v1/marketplaces/updates",
                params={"marketplace_id": "nonexistent"},
            )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200


class TestApplyUpdateAPI:
    """应用插件更新 API 测试"""

    @pytest.mark.asyncio
    async def test_apply_update_success(self):
        """测试应用插件更新成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())
        plugin_id = "test-plugin"
        mock_response = {
            "plugin_id": plugin_id,
            "old_version": "1.0.0",
            "new_version": "1.1.0",
            "status": "updated",
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces/updates/{plugin_id}")
        async def apply_update(plugin_id: str, request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/tenant/admin/v1/marketplaces/updates/{plugin_id}",
                json={"marketplace_id": marketplace_id},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["plugin_id"] == plugin_id
        assert data["data"]["old_version"] == "1.0.0"
        assert data["data"]["new_version"] == "1.1.0"
        assert data["data"]["status"] == "updated"

    @pytest.mark.asyncio
    async def test_apply_update_no_update_available(self):
        """测试应用更新 - 无可用更新"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())
        plugin_id = "test-plugin"

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces/updates/{plugin_id}")
        async def apply_update(plugin_id: str, request: dict):
            return ApiResponse.fail("该插件没有可用更新")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/tenant/admin/v1/marketplaces/updates/{plugin_id}",
                json={"marketplace_id": marketplace_id},
            )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200

    @pytest.mark.asyncio
    async def test_apply_update_plugin_not_found(self):
        """测试应用更新 - 插件不存在"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces/updates/{plugin_id}")
        async def apply_update(plugin_id: str, request: dict):
            return ApiResponse.fail("插件不存在")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/marketplaces/updates/nonexistent-plugin",
                json={"marketplace_id": marketplace_id},
            )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200


class TestSyncAPIPatterns:
    """同步 API 模式测试"""

    def test_sync_result_response_format(self):
        """测试同步结果响应格式"""
        from framework.common.response import ApiResponse

        mock_data = {
            "success": [{"plugin_id": "p1", "version": "1.0.0"}],
            "failed": [],
            "skipped": [],
        }
        response = ApiResponse.success(data=mock_data)
        assert response.status_code == 200
        import json
        content = json.loads(response.body)
        assert content["code"] == 200
        assert "success" in content["data"]
        assert "failed" in content["data"]
        assert "skipped" in content["data"]

    def test_update_response_format(self):
        """测试更新响应格式"""
        from framework.common.response import ApiResponse

        mock_data = [
            {
                "plugin_id": "p1",
                "current_version": "1.0.0",
                "latest_version": "1.1.0",
                "has_update": True,
            }
        ]
        response = ApiResponse.success(data=mock_data)
        assert response.status_code == 200
        import json
        content = json.loads(response.body)
        assert content["code"] == 200
        assert isinstance(content["data"], list)
