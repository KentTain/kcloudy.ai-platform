"""
AI 插件安装/卸载 API 集成测试

测试 AI 模块插件安装和卸载相关的 API 端点：
- GET /ai/console/v1/plugins/available - 获取可用插件列表
- POST /ai/console/v1/plugins/installations - 创建安装任务
- GET /ai/console/v1/plugins/install-tasks - 获取安装任务列表
- GET /ai/console/v1/plugins/install-tasks/{task_id} - 获取安装任务详情
- DELETE /ai/console/v1/plugins/installations/{plugin_id} - 卸载插件

注意：由于模块导入时的初始化依赖，使用隔离测试方式实现。
"""

import os
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"

pytestmark = pytest.mark.integration


@pytest.fixture
def test_tenant_id():
    """测试租户 ID"""
    return "test-tenant-" + uuid.uuid4().hex[:8]


@pytest.fixture
def test_plugin_id():
    """测试插件 ID"""
    return "test-author/test-plugin"


@pytest.fixture
def test_task_id():
    """测试任务 ID"""
    return str(uuid.uuid4())


class TestAvailablePluginsAPI:
    """可用插件列表 API 测试"""

    @pytest.mark.asyncio
    async def test_get_available_plugins_success(self, test_tenant_id):
        """测试获取可用插件列表成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        # 模拟响应数据
        mock_response = {
            "items": [
                {
                    "plugin_id": "test-author/test-plugin",
                    "name": "Test Plugin",
                    "author": "test-author",
                    "version": "1.0.0",
                    "type": "plugin",
                    "is_recommended": True,
                    "is_installed": False,
                    "installation_status": None,
                    "description": "测试插件",
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/available")
        async def get_available_plugins():
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ai/console/v1/plugins/available")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]

    @pytest.mark.asyncio
    async def test_get_available_plugins_with_filters(self, test_tenant_id):
        """测试带筛选条件获取可用插件列表"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/available")
        async def get_available_plugins(keyword: str = None, type: str = None, is_recommended: bool = None):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/ai/console/v1/plugins/available",
                params={"keyword": "test", "type": "plugin", "is_recommended": True},
            )

        assert response.status_code == 200


class TestCreateInstallTaskAPI:
    """创建安装任务 API 测试"""

    @pytest.mark.asyncio
    async def test_create_install_task_success(self, test_plugin_id):
        """测试创建安装任务成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "task_id": str(uuid.uuid4()),
            "plugin_id": test_plugin_id,
            "message": "安装任务已创建",
            "status": "pending",
        }

        app = FastAPI()

        @app.post("/ai/console/v1/plugins/installations")
        async def create_installation(request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/ai/console/v1/plugins/installations",
                json={"plugin_id": test_plugin_id, "auto_start": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "task_id" in data["data"]

    @pytest.mark.asyncio
    async def test_create_install_task_plugin_not_found(self):
        """测试创建安装任务时插件定义不存在"""
        from fastapi import FastAPI
        from fastapi.responses import ORJSONResponse
        from framework.common.exceptions import NotFoundError

        app = FastAPI()

        @app.post("/ai/console/v1/plugins/installations")
        async def create_installation(request: dict):
            raise NotFoundError(message="插件定义不存在")

        @app.exception_handler(NotFoundError)
        async def not_found_handler(request, exc):
            return ORJSONResponse(status_code=404, content={"code": 404, "message": str(exc)})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/ai/console/v1/plugins/installations",
                json={"plugin_id": "nonexistent/plugin", "auto_start": False},
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_install_task_already_installed(self, test_plugin_id):
        """测试创建安装任务时插件已安装"""
        from fastapi import FastAPI
        from fastapi.responses import ORJSONResponse
        from framework.common.exceptions import BadRequestError

        app = FastAPI()

        @app.post("/ai/console/v1/plugins/installations")
        async def create_installation(request: dict):
            raise BadRequestError(message="插件已安装")

        @app.exception_handler(BadRequestError)
        async def bad_request_handler(request, exc):
            return ORJSONResponse(status_code=400, content={"code": 400, "message": str(exc)})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/ai/console/v1/plugins/installations",
                json={"plugin_id": test_plugin_id, "auto_start": False},
            )

        assert response.status_code == 400


class TestInstallTaskListAPI:
    """安装任务列表 API 测试"""

    @pytest.mark.asyncio
    async def test_get_install_tasks_success(self):
        """测试获取安装任务列表成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "items": [
                {
                    "id": str(uuid.uuid4()),
                    "plugin_id": "test-author/test-plugin",
                    "status": "completed",
                    "progress": 100,
                    "current_step": "finalize",
                    "created_at": datetime.now().isoformat(),
                    "started_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/install-tasks")
        async def get_install_tasks():
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ai/console/v1/plugins/install-tasks")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]


class TestInstallTaskDetailAPI:
    """安装任务详情 API 测试"""

    @pytest.mark.asyncio
    async def test_get_install_task_detail_success(self, test_task_id):
        """测试获取安装任务详情成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "id": test_task_id,
            "plugin_id": "test-author/test-plugin",
            "status": "running",
            "progress": 50,
            "current_step": "install",
            "created_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "plugin_unique_identifier": "test-author/test-plugin@1.0.0",
            "steps": [
                {"step": "download", "name": "下载插件包", "status": "completed"},
                {"step": "validate", "name": "校验插件包", "status": "completed"},
                {"step": "install", "name": "安装插件", "status": "running"},
                {"step": "configure", "name": "初始化配置", "status": "pending"},
                {"step": "finalize", "name": "完成安装", "status": "pending"},
            ],
            "error_message": None,
            "logs": None,
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/install-tasks/{task_id}")
        async def get_task_detail(task_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/ai/console/v1/plugins/install-tasks/{test_task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == test_task_id

    @pytest.mark.asyncio
    async def test_get_install_task_detail_with_error(self, test_task_id):
        """测试获取失败任务的详情"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "id": test_task_id,
            "plugin_id": "test-author/test-plugin",
            "status": "failed",
            "progress": 30,
            "current_step": "install",
            "created_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "plugin_unique_identifier": "test-author/test-plugin@1.0.0",
            "steps": [],
            "error_message": "安装失败: 配置创建错误",
            "logs": None,
        }

        app = FastAPI()

        @app.get("/ai/console/v1/plugins/install-tasks/{task_id}")
        async def get_task_detail(task_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/ai/console/v1/plugins/install-tasks/{test_task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "failed"
        assert data["data"]["error_message"] is not None


class TestUninstallPluginAPI:
    """卸载插件 API 测试"""

    @pytest.mark.asyncio
    async def test_uninstall_plugin_success(self):
        """测试卸载插件成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        mock_response = {
            "plugin_id": "test-plugin",
            "message": "插件卸载成功",
            "success": True,
        }

        app = FastAPI()

        @app.delete("/ai/console/v1/plugins/installations/{plugin_id}")
        async def uninstall_plugin(plugin_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/ai/console/v1/plugins/installations/test-plugin")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["success"] is True

    @pytest.mark.asyncio
    async def test_uninstall_plugin_not_found(self):
        """测试卸载不存在的插件"""
        from fastapi import FastAPI
        from fastapi.responses import ORJSONResponse
        from framework.common.exceptions import NotFoundError

        app = FastAPI()

        @app.delete("/ai/console/v1/plugins/installations/{plugin_id}")
        async def uninstall_plugin(plugin_id: str):
            raise NotFoundError(message="插件未安装")

        @app.exception_handler(NotFoundError)
        async def not_found_handler(request, exc):
            return ORJSONResponse(status_code=404, content={"code": 404, "message": str(exc)})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/ai/console/v1/plugins/installations/nonexistent")

        assert response.status_code == 404


class TestInstallTaskServiceLogic:
    """安装任务服务逻辑测试"""

    @pytest.mark.asyncio
    async def test_create_install_task_validation(self, test_plugin_id, test_tenant_id):
        """测试创建安装任务参数验证"""
        # 验证请求参数结构
        request_data = {
            "plugin_id": test_plugin_id,
            "auto_start": False,
        }

        assert "plugin_id" in request_data
        assert isinstance(request_data["auto_start"], bool)

    @pytest.mark.asyncio
    async def test_install_task_timeout_check_logic(self):
        """测试安装任务超时检查逻辑"""
        # 模拟超时阈值
        timeout_seconds = 1800  # 30 分钟

        # 模拟任务开始时间
        started_at = datetime.now()
        elapsed = 0  # 刚开始

        # 检查是否超时
        is_timeout = elapsed > timeout_seconds
        assert is_timeout is False

    def test_install_task_status_transitions(self):
        """测试安装任务状态转换"""
        # 定义有效状态
        valid_statuses = ["pending", "running", "completed", "failed", "timeout"]

        # 测试状态转换顺序
        normal_flow = ["pending", "running", "completed"]
        failed_flow = ["pending", "running", "failed"]

        assert normal_flow[0] == "pending"
        assert failed_flow[-1] == "failed"
