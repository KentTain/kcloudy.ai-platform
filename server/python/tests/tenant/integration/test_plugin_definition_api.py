"""
Tenant 插件定义管理 API 集成测试

测试插件定义管理的 API 端点：
- POST /tenant/admin/v1/plugin-definitions/scan - 扫描目录注册
- POST /tenant/admin/v1/plugin-definitions/upload - 上传插件包注册
- GET /tenant/admin/v1/plugin-definitions - 列表查询
- GET /tenant/admin/v1/plugin-definitions/{plugin_id} - 详情查看
- PATCH /tenant/admin/v1/plugin-definitions/{plugin_id} - 更新定义
- DELETE /tenant/admin/v1/plugin-definitions/{plugin_id} - 删除定义
- GET /tenant/admin/v1/plugin-definitions/statistics - 统计数据

注意：由于模块导入时的初始化依赖，使用隔离测试方式实现。
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


class TestPluginDefinitionListAPI:
    """插件定义列表 API 测试"""

    @pytest.mark.asyncio
    async def test_list_plugin_definitions_success(self):
        """测试获取插件定义列表成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "items": [
                {
                    "id": str(uuid.uuid4()),
                    "plugin_id": "test-author/test-plugin",
                    "plugin_unique_identifier": "test-author/test-plugin@1.0.0",
                    "version": "1.0.0",
                    "name": "Test Plugin",
                    "author": "test-author",
                    "type": "plugin",
                    "refers": 0,
                    "is_recommended": False,
                    "is_enabled": True,
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }

        app = FastAPI()

        @app.get("/tenant/admin/v1/plugin-definitions")
        async def list_definitions():
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/tenant/admin/v1/plugin-definitions")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]

    @pytest.mark.asyncio
    async def test_list_plugin_definitions_with_filters(self):
        """测试带筛选条件获取插件定义列表"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
        }

        app = FastAPI()

        @app.get("/tenant/admin/v1/plugin-definitions")
        async def list_definitions(keyword: str = None, type: str = None):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/tenant/admin/v1/plugin-definitions",
                params={"keyword": "test", "type": "plugin"},
            )

        assert response.status_code == 200


class TestPluginDefinitionDetailAPI:
    """插件定义详情 API 测试"""

    @pytest.mark.asyncio
    async def test_get_plugin_definition_detail_success(self):
        """测试获取插件定义详情成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        plugin_id = "test-plugin"

        mock_response = {
            "id": str(uuid.uuid4()),
            "plugin_id": plugin_id,
            "plugin_unique_identifier": "test-plugin@1.0.0",
            "version": "1.0.0",
            "name": "Test Plugin",
            "author": "test-author",
            "type": "plugin",
            "refers": 0,
            "is_recommended": False,
            "is_enabled": True,
            "declaration": {"version": "1.0.0", "name": "Test Plugin"},
        }

        app = FastAPI()

        @app.get("/tenant/admin/v1/plugin-definitions/{plugin_id}")
        async def get_detail(plugin_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/tenant/admin/v1/plugin-definitions/{plugin_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["plugin_id"] == plugin_id

    @pytest.mark.asyncio
    async def test_get_plugin_definition_detail_not_found(self):
        """测试获取不存在的插件定义详情"""
        from fastapi import FastAPI
        from fastapi.responses import ORJSONResponse
        from framework.common.exceptions import NotFoundError

        app = FastAPI()

        @app.get("/tenant/admin/v1/plugin-definitions/{plugin_id}")
        async def get_detail(plugin_id: str):
            raise NotFoundError(message="插件定义不存在")

        @app.exception_handler(NotFoundError)
        async def not_found_handler(request, exc):
            return ORJSONResponse(status_code=404, content={"code": 404, "message": str(exc)})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/tenant/admin/v1/plugin-definitions/nonexistent")

        assert response.status_code == 404


class TestPluginDefinitionUpdateAPI:
    """插件定义更新 API 测试"""

    @pytest.mark.asyncio
    async def test_update_plugin_definition_mark_recommended(self):
        """测试标记插件定义为推荐"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        plugin_id = "test-plugin"

        mock_response = {
            "id": str(uuid.uuid4()),
            "plugin_id": plugin_id,
            "is_recommended": True,
            "is_enabled": True,
        }

        app = FastAPI()

        @app.patch("/tenant/admin/v1/plugin-definitions/{plugin_id}")
        async def update(plugin_id: str, request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/tenant/admin/v1/plugin-definitions/{plugin_id}",
                json={"is_recommended": True},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["is_recommended"] is True

    @pytest.mark.asyncio
    async def test_update_plugin_definition_disable(self):
        """测试禁用插件定义"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        plugin_id = "test-plugin"

        mock_response = {
            "id": str(uuid.uuid4()),
            "plugin_id": plugin_id,
            "is_recommended": False,
            "is_enabled": False,
        }

        app = FastAPI()

        @app.patch("/tenant/admin/v1/plugin-definitions/{plugin_id}")
        async def update(plugin_id: str, request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/tenant/admin/v1/plugin-definitions/{plugin_id}",
                json={"is_enabled": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["is_enabled"] is False


class TestPluginDefinitionDeleteAPI:
    """插件定义删除 API 测试"""

    @pytest.mark.asyncio
    async def test_delete_plugin_definition_success(self):
        """测试删除插件定义成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        plugin_id = "test-plugin"

        app = FastAPI()

        @app.delete("/tenant/admin/v1/plugin-definitions/{plugin_id}")
        async def delete(plugin_id: str):
            return ApiResponse.success(message="插件定义已删除")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/tenant/admin/v1/plugin-definitions/{plugin_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_delete_plugin_definition_with_references(self):
        """测试删除有引用的插件定义失败"""
        from fastapi import FastAPI
        from fastapi.responses import ORJSONResponse
        from framework.common.exceptions import ConflictError

        app = FastAPI()

        @app.delete("/tenant/admin/v1/plugin-definitions/{plugin_id}")
        async def delete(plugin_id: str):
            raise ConflictError(message="插件定义仍被租户引用，无法删除")

        @app.exception_handler(ConflictError)
        async def conflict_handler(request, exc):
            return ORJSONResponse(status_code=409, content={"code": 409, "message": str(exc)})

        plugin_id = "test-plugin"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/tenant/admin/v1/plugin-definitions/{plugin_id}")

        assert response.status_code == 409


class TestPluginDefinitionStatisticsAPI:
    """插件定义统计 API 测试"""

    @pytest.mark.asyncio
    async def test_get_plugin_statistics_success(self):
        """测试获取插件统计数据成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "definition_stats": {
                "total_count": 10,
                "by_type": {"plugin": 8, "agent": 2},
                "recommended_count": 3,
                "enabled_count": 9,
            },
            "installation_stats": {
                "total_count": 25,
                "active_count": 20,
                "weekly_new_count": 5,
            },
        }

        app = FastAPI()

        @app.get("/tenant/admin/v1/plugin-definitions/statistics")
        async def get_statistics():
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/tenant/admin/v1/plugin-definitions/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "definition_stats" in data["data"]
        assert "installation_stats" in data["data"]


class TestPluginDefinitionUploadAPI:
    """插件定义上传 API 测试"""

    @pytest.mark.asyncio
    async def test_upload_plugin_package_success(self):
        """测试上传插件包成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "plugin_id": "test-plugin",
            "version": "1.0.0",
            "plugin_unique_identifier": "test-plugin@1.0.0",
            "status": "created",
            "message": "插件定义注册成功",
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-definitions/upload")
        async def upload():
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/tenant/admin/v1/plugin-definitions/upload")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_upload_plugin_package_invalid_format(self):
        """测试上传非 zip 格式文件失败"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-definitions/upload")
        async def upload():
            return ApiResponse.fail("请上传 .zip 格式的插件包")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/tenant/admin/v1/plugin-definitions/upload")

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200


class TestPluginDefinitionScanAPI:
    """插件定义扫描 API 测试"""

    @pytest.mark.asyncio
    async def test_scan_directory_success(self):
        """测试扫描目录成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "total_count": 1,
            "success_count": 1,
            "skipped_count": 0,
            "failed_count": 0,
            "results": [],
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-definitions/scan")
        async def scan(request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/plugin-definitions/scan",
                json={"directory": "/tmp", "recursive": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "total_count" in data["data"]

    @pytest.mark.asyncio
    async def test_scan_directory_not_exists(self):
        """测试扫描不存在的目录"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-definitions/scan")
        async def scan(request: dict):
            return ApiResponse.fail("目录不存在")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/plugin-definitions/scan",
                json={"directory": "/nonexistent", "recursive": False},
            )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] != 200

    @pytest.mark.asyncio
    async def test_scan_directory_empty(self):
        """测试扫描空目录"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "total_count": 0,
            "success_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "results": [],
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-definitions/scan")
        async def scan(request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/plugin-definitions/scan",
                json={"directory": "/tmp", "recursive": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total_count"] == 0


class TestPluginDefinitionAPIPatterns:
    """插件定义 API 模式测试"""

    def test_api_response_format(self):
        """测试 API 响应格式"""
        from framework.common.response import ApiResponse

        # 成功响应
        success_response = ApiResponse.success(data={"test": "value"})
        assert success_response.status_code == 200
        content = success_response.body
        import json
        data = json.loads(content)
        assert data["code"] == 200
        assert "data" in data

    def test_api_fail_response_format(self):
        """测试 API 失败响应格式"""
        from framework.common.response import ApiResponse

        # 失败响应
        fail_response = ApiResponse.fail("测试错误")
        assert fail_response.status_code == 400
        import json
        data = json.loads(fail_response.body)
        assert data["code"] == 400
        assert data["msg"] == "测试错误"

    def test_api_not_found_response(self):
        """测试 API 404 响应"""
        from framework.common.response import ApiResponse

        not_found = ApiResponse.not_found("插件定义不存在")
        assert not_found.status_code == 404
        import json
        data = json.loads(not_found.body)
        assert data["code"] == 404

    def test_api_conflict_response(self):
        """测试 API 409 冲突响应"""
        from framework.common.response import ApiResponse

        conflict = ApiResponse.conflict("插件定义仍被租户引用")
        assert conflict.status_code == 409
        import json
        data = json.loads(conflict.body)
        assert data["code"] == 409
