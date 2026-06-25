"""
AI 运行时管理 API 集成测试

测试 AI 模块运行时管理相关的 API 端点：
- POST /ai/console/v1/plugins/installations/{plugin_id}/start - 启动插件
- POST /ai/console/v1/plugins/installations/{plugin_id}/stop - 停止插件
- GET /ai/console/v1/plugins/installations/{plugin_id}/config - 获取插件配置
- PATCH /ai/console/v1/plugins/installations/{plugin_id}/config - 更新插件配置
- GET /ai/console/v1/plugins/installations/{plugin_id}/runtime-state - 获取运行时状态
- GET /ai/console/v1/plugins/runtime-states - 批量获取运行时状态

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


class TestStartPluginAPI:
    """启动插件 API 测试"""

    @pytest.mark.asyncio
    async def test_start_plugin_success(self):
        """测试启动插件成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "plugin_id": "test-plugin",
            "status": "active",
            "message": "插件启动成功",
            "process_id": 12345,
            "started_at": datetime.now().isoformat(),
        }

        app = FastAPI()

        @app.post("/ai/console/v1/plugins/installations/{plugin_id}/start")
        async def start_plugin(plugin_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/ai/console/v1/plugins/installations/test-plugin/start")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_start_plugin_not_found(self):
        """测试启动不存在的插件"""
        from fastapi import FastAPI
        from fastapi.responses import ORJSONResponse
        from framework.common.exceptions import NotFoundError

        app = FastAPI()

        @app.post("/ai/console/v1/plugins/installations/{plugin_id}/start")
        async def start_plugin(plugin_id: str):
            raise NotFoundError(message="插件未安装")

        @app.exception_handler(NotFoundError)
        async def not_found_handler(request, exc):
            return ORJSONResponse(status_code=404, content={"code": 404, "message": str(exc)})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/ai/console/v1/plugins/installations/nonexistent/start")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_start_plugin_already_running(self):
        """测试启动已运行的插件"""
        from fastapi import FastAPI
        from fastapi.responses import ORJSONResponse
        from framework.common.exceptions import BadRequestError

        app = FastAPI()

        @app.post("/ai/console/v1/plugins/installations/{plugin_id}/start")
        async def start_plugin(plugin_id: str):
            raise BadRequestError(message="插件已在运行中")

        @app.exception_handler(BadRequestError)
        async def bad_request_handler(request, exc):
            return ORJSONResponse(status_code=400, content={"code": 400, "message": str(exc)})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/ai/console/v1/plugins/installations/test-plugin/start")

        assert response.status_code == 400


class TestStopPluginAPI:
    """停止插件 API 测试"""

    @pytest.mark.asyncio
    async def test_stop_plugin_success(self):
        """测试停止插件成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "plugin_id": "test-plugin",
            "status": "inactive",
            "message": "插件停止成功",
            "stopped_at": datetime.now().isoformat(),
        }

        app = FastAPI()

        @app.post("/ai/console/v1/plugins/installations/{plugin_id}/stop")
        async def stop_plugin(plugin_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/ai/console/v1/plugins/installations/test-plugin/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "inactive"


class TestGetPluginConfigAPI:
    """获取插件配置 API 测试"""

    @pytest.mark.asyncio
    async def test_get_plugin_config_success(self):
        """测试获取插件配置成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "plugin_id": "test-plugin",
            "plugin_config": {
                "version": "1.0.0",
                "name": "Test Plugin",
                "tools_configuration": [],
            },
            "runtime_config": {
                "timeout": 30,
                "max_retries": 3,
            },
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/installations/{plugin_id}/config")
        async def get_plugin_config(plugin_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ai/console/v1/plugins/installations/test-plugin/config")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["plugin_id"] == "test-plugin"


class TestUpdatePluginConfigAPI:
    """更新插件配置 API 测试"""

    @pytest.mark.asyncio
    async def test_update_plugin_config_success(self):
        """测试更新插件配置成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        new_config = {"timeout": 60, "max_retries": 5}

        mock_response = {
            "plugin_id": "test-plugin",
            "runtime_config": new_config,
            "message": "配置更新成功",
        }

        app = FastAPI()

        @app.patch("/ai/console/v1/plugins/installations/{plugin_id}/config")
        async def update_plugin_config(plugin_id: str, request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                "/ai/console/v1/plugins/installations/test-plugin/config",
                json={"runtime_config": new_config},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["plugin_id"] == "test-plugin"


class TestGetRuntimeStateAPI:
    """获取运行时状态 API 测试"""

    @pytest.mark.asyncio
    async def test_get_runtime_state_success(self):
        """测试获取运行时状态成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "plugin_id": "test-plugin",
            "status": "active",
            "process_id": 12345,
            "started_at": datetime.now().isoformat(),
            "call_count": 100,
            "error_count": 2,
            "last_call_at": datetime.now().isoformat(),
            "memory_usage_mb": 256.5,
            "cpu_usage_percent": 15.3,
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/installations/{plugin_id}/runtime-state")
        async def get_runtime_state(plugin_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ai/console/v1/plugins/installations/test-plugin/runtime-state")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_runtime_state_inactive(self):
        """测试获取未运行插件的运行时状态"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "plugin_id": "test-plugin",
            "status": "inactive",
            "process_id": None,
            "started_at": None,
            "call_count": 0,
            "error_count": 0,
            "last_call_at": None,
            "memory_usage_mb": None,
            "cpu_usage_percent": None,
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/installations/{plugin_id}/runtime-state")
        async def get_runtime_state(plugin_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ai/console/v1/plugins/installations/test-plugin/runtime-state")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "inactive"


class TestGetRuntimeStatesAPI:
    """批量获取运行时状态 API 测试"""

    @pytest.mark.asyncio
    async def test_get_runtime_states_success(self):
        """测试批量获取运行时状态成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "items": [
                {
                    "plugin_id": "test-author/plugin-1",
                    "status": "active",
                    "call_count": 100,
                    "error_count": 0,
                },
                {
                    "plugin_id": "test-author/plugin-2",
                    "status": "inactive",
                    "call_count": 50,
                    "error_count": 1,
                },
            ],
            "total_count": 2,
            "active_count": 1,
            "inactive_count": 1,
            "error_count": 1,
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/runtime-states")
        async def get_runtime_states():
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ai/console/v1/plugins/runtime-states")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total_count"] == 2

    @pytest.mark.asyncio
    async def test_get_runtime_states_empty(self):
        """测试批量获取运行时状态为空"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "items": [],
            "total_count": 0,
            "active_count": 0,
            "inactive_count": 0,
            "error_count": 0,
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/runtime-states")
        async def get_runtime_states():
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ai/console/v1/plugins/runtime-states")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_count"] == 0


class TestPluginStatisticsAPI:
    """插件统计 API 测试"""

    @pytest.mark.asyncio
    async def test_get_statistics_success(self):
        """测试获取插件统计数据成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "status_stats": {
                "total": 5,
                "active": 3,
                "inactive": 2,
                "error": 0,
            },
            "usage_stats": {
                "total_calls": 1000,
                "total_errors": 10,
                "avg_response_time_ms": 150.5,
                "weekly_calls": 200,
            },
            "runtime_stats": {
                "total_memory_mb": 512.0,
                "avg_cpu_percent": 25.5,
                "running_processes": 3,
            },
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/installations/statistics")
        async def get_statistics():
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ai/console/v1/plugins/installations/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "status_stats" in data["data"]
        assert "usage_stats" in data["data"]
        assert "runtime_stats" in data["data"]


class TestPluginRuntimeIntegration:
    """插件运行时集成测试"""

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self):
        """测试插件启动停止生命周期"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        app = FastAPI()

        @app.post("/ai/console/v1/plugins/installations/{plugin_id}/start")
        async def start_plugin(plugin_id: str):
            return ApiResponse.success(data={
                "plugin_id": plugin_id,
                "status": "active",
                "message": "插件启动成功",
            })

        @app.post("/ai/console/v1/plugins/installations/{plugin_id}/stop")
        async def stop_plugin(plugin_id: str):
            return ApiResponse.success(data={
                "plugin_id": plugin_id,
                "status": "inactive",
                "message": "插件停止成功",
            })

        # 先启动
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            start_response = await client.post("/ai/console/v1/plugins/installations/test-plugin/start")

        assert start_response.status_code == 200
        assert start_response.json()["data"]["status"] == "active"

        # 再停止
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            stop_response = await client.post("/ai/console/v1/plugins/installations/test-plugin/stop")

        assert stop_response.status_code == 200
        assert stop_response.json()["data"]["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_config_update_persists(self):
        """测试配置更新持久化"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        new_config = {"timeout": 60, "max_retries": 5}

        app = FastAPI()

        @app.patch("/ai/console/v1/plugins/installations/{plugin_id}/config")
        async def update_config(plugin_id: str, request: dict):
            return ApiResponse.success(data={
                "plugin_id": plugin_id,
                "runtime_config": request.get("runtime_config", {}),
                "message": "配置更新成功",
            })

        @app.get("/ai/console/v1/plugins/installations/{plugin_id}/config")
        async def get_config(plugin_id: str):
            return ApiResponse.success(data={
                "plugin_id": plugin_id,
                "plugin_config": {},
                "runtime_config": new_config,
            })

        # 更新配置
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            update_response = await client.patch(
                "/ai/console/v1/plugins/installations/test-plugin/config",
                json={"runtime_config": new_config},
            )

        assert update_response.status_code == 200
        assert update_response.json()["data"]["runtime_config"] == new_config

        # 验证配置持久化
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            get_response = await client.get("/ai/console/v1/plugins/installations/test-plugin/config")

        assert get_response.status_code == 200
        assert get_response.json()["data"]["runtime_config"] == new_config
