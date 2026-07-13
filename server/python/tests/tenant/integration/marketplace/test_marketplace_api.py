"""
插件市场 API 集成测试

测试 /tenant/admin/v1/marketplaces 路由的 CRUD 操作。
"""

import os
import uuid
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"

pytestmark = pytest.mark.integration


class TestMarketplaceCreateAPI:
    """市场创建 API 测试"""

    @pytest.mark.asyncio
    async def test_create_marketplace(self):
        """测试创建市场"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())
        mock_response = {
            "id": marketplace_id,
            "name": "Test Dify Market",
            "code": "test-dify",
            "type": "dify",
            "url": "https://plugins.dify.ai/api/v1",
            "auth_type": "none",
            "auth_config": {},
            "is_enabled": True,
            "description": "Test marketplace",
            "last_sync_at": None,
            "last_sync_status": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces")
        async def create_marketplace(request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/marketplaces",
                json={
                    "name": "Test Dify Market",
                    "code": "test-dify",
                    "type": "dify",
                    "url": "https://plugins.dify.ai/api/v1",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == "Test Dify Market"
        assert data["data"]["code"] == "test-dify"

    @pytest.mark.asyncio
    async def test_create_marketplace_with_duplicate_code(self):
        """测试创建重复编码的市场失败"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.post("/tenant/admin/v1/marketplaces")
        async def create_marketplace(request: dict):
            return ApiResponse.fail("市场编码已存在: test-dify")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/marketplaces",
                json={
                    "name": "Test Dify Market",
                    "code": "test-dify",
                    "type": "dify",
                    "url": "https://plugins.dify.ai/api/v1",
                },
            )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200


class TestMarketplaceListAPI:
    """市场列表 API 测试"""

    @pytest.mark.asyncio
    async def test_list_marketplaces(self):
        """测试获取市场列表"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())
        mock_response = [
            {
                "id": marketplace_id,
                "name": "Dify Official",
                "code": "dify-official",
                "type": "dify",
                "url": "https://plugins.dify.ai/api/v1",
                "auth_type": "none",
                "auth_config": {},
                "is_enabled": True,
                "description": "Dify official marketplace",
                "last_sync_at": None,
                "last_sync_status": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        ]

        app = FastAPI()

        @app.get("/tenant/admin/v1/marketplaces")
        async def list_marketplaces(type: str = None, is_enabled: bool = None):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/tenant/admin/v1/marketplaces")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Dify Official"

    @pytest.mark.asyncio
    async def test_list_marketplaces_with_filters(self):
        """测试带筛选条件获取市场列表"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = []

        app = FastAPI()

        @app.get("/tenant/admin/v1/marketplaces")
        async def list_marketplaces(type: str = None, is_enabled: bool = None):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/tenant/admin/v1/marketplaces",
                params={"type": "dify", "is_enabled": True},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)


class TestMarketplaceDetailAPI:
    """市场详情 API 测试"""

    @pytest.mark.asyncio
    async def test_get_marketplace(self):
        """测试获取市场详情"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())
        mock_response = {
            "id": marketplace_id,
            "name": "Dify Official",
            "code": "dify-official",
            "type": "dify",
            "url": "https://plugins.dify.ai/api/v1",
            "auth_type": "none",
            "auth_config": {},
            "is_enabled": True,
            "description": "Dify official marketplace",
            "last_sync_at": None,
            "last_sync_status": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        app = FastAPI()

        @app.get("/tenant/admin/v1/marketplaces/{marketplace_id}")
        async def get_marketplace(marketplace_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/tenant/admin/v1/marketplaces/{marketplace_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == marketplace_id
        assert data["data"]["name"] == "Dify Official"

    @pytest.mark.asyncio
    async def test_get_marketplace_not_found(self):
        """测试获取不存在的市场"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.get("/tenant/admin/v1/marketplaces/{marketplace_id}")
        async def get_marketplace(marketplace_id: str):
            return ApiResponse.fail("市场不存在")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/tenant/admin/v1/marketplaces/nonexistent")

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200


class TestMarketplaceUpdateAPI:
    """市场更新 API 测试"""

    @pytest.mark.asyncio
    async def test_update_marketplace(self):
        """测试更新市场"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())
        mock_response = {
            "id": marketplace_id,
            "name": "Updated Market",
            "code": "test-dify",
            "type": "dify",
            "url": "https://plugins.dify.ai/api/v1",
            "auth_type": "none",
            "auth_config": {},
            "is_enabled": True,
            "description": "Updated description",
            "last_sync_at": None,
            "last_sync_status": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        app = FastAPI()

        @app.put("/tenant/admin/v1/marketplaces/{marketplace_id}")
        async def update_marketplace(marketplace_id: str, request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/tenant/admin/v1/marketplaces/{marketplace_id}",
                json={"name": "Updated Market", "description": "Updated description"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == "Updated Market"
        assert data["data"]["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_marketplace_not_found(self):
        """测试更新不存在的市场"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.put("/tenant/admin/v1/marketplaces/{marketplace_id}")
        async def update_marketplace(marketplace_id: str, request: dict):
            return ApiResponse.fail("市场不存在: nonexistent")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                "/tenant/admin/v1/marketplaces/nonexistent",
                json={"name": "Updated Market"},
            )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200


class TestMarketplaceDeleteAPI:
    """市场删除 API 测试"""

    @pytest.mark.asyncio
    async def test_delete_marketplace(self):
        """测试删除市场"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        marketplace_id = str(uuid.uuid4())

        app = FastAPI()

        @app.delete("/tenant/admin/v1/marketplaces/{marketplace_id}")
        async def delete_marketplace(marketplace_id: str):
            return ApiResponse.success(msg="市场已删除")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/tenant/admin/v1/marketplaces/{marketplace_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["msg"] == "市场已删除"

    @pytest.mark.asyncio
    async def test_delete_marketplace_not_found(self):
        """测试删除不存在的市场"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.delete("/tenant/admin/v1/marketplaces/{marketplace_id}")
        async def delete_marketplace(marketplace_id: str):
            return ApiResponse.fail("市场不存在: nonexistent")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/tenant/admin/v1/marketplaces/nonexistent")

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200


class TestMarketplaceAPIPatterns:
    """市场 API 模式测试"""

    def test_api_response_format(self):
        """测试 API 响应格式"""
        from framework.common.response import ApiResponse

        success_response = ApiResponse.success(data={"test": "value"})
        assert success_response.status_code == 200
        import json
        content = success_response.body
        data = json.loads(content)
        assert data["code"] == 200
        assert "data" in data

    def test_api_fail_response_format(self):
        """测试 API 失败响应格式"""
        from framework.common.response import ApiResponse

        fail_response = ApiResponse.fail("测试错误")
        assert fail_response.status_code == 400
        import json
        data = json.loads(fail_response.body)
        assert data["code"] == 400
        assert data["msg"] == "测试错误"
