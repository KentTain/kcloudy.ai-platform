"""
资源配置 API 路由集成测试

测试 /resources/* 路由的 CRUD 操作和连通性测试接口。
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from tenant.controllers.admin.resource_controller import router


# 创建测试应用
app = FastAPI()
app.include_router(router)


class TestDatabaseResourceRoutes:
    """数据库资源配置路由测试"""

    @pytest.fixture
    def mock_admin(self):
        """模拟管理员认证"""
        return {"id": "admin-1", "username": "admin"}

    @pytest.fixture
    def mock_db_config(self):
        """模拟数据库配置"""
        config = MagicMock()
        config.id = "db-1"
        config.name = "测试数据库"
        config.type = "postgresql"
        config.host = "localhost"
        config.port = 5432
        config.database = "test_db"
        config.username = "admin"
        config.password = "******"
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        return config

    @pytest.mark.asyncio
    async def test_list_database_configs_route_accessible(self, mock_admin, mock_db_config):
        """测试 GET /resources/databases 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.list_configs",
            new_callable=AsyncMock,
            return_value=([mock_db_config], 1),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/resources/databases")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]
        assert data["data"]["total"] == 1

    @pytest.mark.asyncio
    async def test_create_database_config_route_accessible(self, mock_admin, mock_db_config):
        """测试 POST /resources/databases 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.create",
            new_callable=AsyncMock,
            return_value=mock_db_config,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.build_response",
            return_value={
                "id": "db-1",
                "name": "测试数据库",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "username": "admin",
                "password": "******",
            },
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/resources/databases",
                    json={
                        "name": "测试数据库",
                        "type": "postgresql",
                        "host": "localhost",
                        "port": 5432,
                        "database": "test_db",
                        "username": "admin",
                        "password": "plain_password",
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == "db-1"

    @pytest.mark.asyncio
    async def test_get_database_config_by_id_route_accessible(self, mock_admin, mock_db_config):
        """测试 GET /resources/databases/{id} 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_db_config,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.build_response",
            return_value={
                "id": "db-1",
                "name": "测试数据库",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "username": "admin",
                "password": "******",
            },
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/resources/databases/db-1")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == "db-1"

    @pytest.mark.asyncio
    async def test_update_database_config_route_accessible(self, mock_admin, mock_db_config):
        """测试 PUT /resources/databases/{id} 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.update",
            new_callable=AsyncMock,
            return_value=mock_db_config,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.build_response",
            return_value={
                "id": "db-1",
                "name": "更新后的数据库",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "username": "admin",
                "password": "******",
            },
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.put(
                    "/resources/databases/db-1", json={"name": "更新后的数据库"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_delete_database_config_route_accessible(self, mock_admin):
        """测试 DELETE /resources/databases/{id} 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.delete",
            new_callable=AsyncMock,
            return_value=True,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.delete("/resources/databases/db-1")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_test_database_connection_route_accessible(self, mock_admin):
        """测试 POST /resources/databases/{id}/test-connection 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.test_connection",
            new_callable=AsyncMock,
            return_value=(True, "连接成功", 10.5),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post("/resources/databases/db-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["success"] is True
        assert data["data"]["latency_ms"] == 10.5

    @pytest.mark.asyncio
    async def test_get_database_config_not_found(self, mock_admin):
        """测试 GET /resources/databases/{id} 配置不存在返回 404"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/resources/databases/nonexistent")

        assert response.status_code == 404


class TestStorageResourceRoutes:
    """存储资源配置路由测试"""

    @pytest.fixture
    def mock_admin(self):
        return {"id": "admin-1", "username": "admin"}

    @pytest.fixture
    def mock_storage_config(self):
        config = MagicMock()
        config.id = "storage-1"
        config.name = "测试存储"
        config.type = "minio"
        config.bucket = "test-bucket"
        config.endpoint = "http://localhost:9000"
        config.access_key = "admin"
        config.secret_key = "******"
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        return config

    @pytest.mark.asyncio
    async def test_list_storage_configs_route_accessible(self, mock_admin, mock_storage_config):
        """测试 GET /resources/storages 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.storage_config_service.StorageConfigService.list_configs",
            new_callable=AsyncMock,
            return_value=([mock_storage_config], 1),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/resources/storages")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]

    @pytest.mark.asyncio
    async def test_test_storage_connection_route_accessible(self, mock_admin):
        """测试 POST /resources/storages/{id}/test-connection 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.storage_config_service.StorageConfigService.test_connection",
            new_callable=AsyncMock,
            return_value=(True, "连接成功", 15.0),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post("/resources/storages/storage-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] is True


class TestCacheResourceRoutes:
    """缓存资源配置路由测试"""

    @pytest.fixture
    def mock_admin(self):
        return {"id": "admin-1", "username": "admin"}

    @pytest.fixture
    def mock_cache_config(self):
        config = MagicMock()
        config.id = "cache-1"
        config.name = "测试缓存"
        config.host = "localhost"
        config.port = 6379
        config.password = "******"
        config.db = 0
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        return config

    @pytest.mark.asyncio
    async def test_list_cache_configs_route_accessible(self, mock_admin, mock_cache_config):
        """测试 GET /resources/caches 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.cache_config_service.CacheConfigService.list_configs",
            new_callable=AsyncMock,
            return_value=([mock_cache_config], 1),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/resources/caches")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_test_cache_connection_route_accessible(self, mock_admin):
        """测试 POST /resources/caches/{id}/test-connection 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.cache_config_service.CacheConfigService.test_connection",
            new_callable=AsyncMock,
            return_value=(True, "连接成功", 5.0),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post("/resources/caches/cache-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] is True


class TestQueueResourceRoutes:
    """队列资源配置路由测试"""

    @pytest.fixture
    def mock_admin(self):
        return {"id": "admin-1", "username": "admin"}

    @pytest.fixture
    def mock_queue_config(self):
        config = MagicMock()
        config.id = "queue-1"
        config.name = "测试队列"
        config.type = "rabbitmq"
        config.host = "localhost"
        config.port = 5672
        config.username = "admin"
        config.password = "******"
        config.vhost = "/"
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        return config

    @pytest.mark.asyncio
    async def test_list_queue_configs_route_accessible(self, mock_admin, mock_queue_config):
        """测试 GET /resources/queues 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.queue_config_service.QueueConfigService.list_configs",
            new_callable=AsyncMock,
            return_value=([mock_queue_config], 1),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/resources/queues")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_test_queue_connection_route_accessible(self, mock_admin):
        """测试 POST /resources/queues/{id}/test-connection 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.queue_config_service.QueueConfigService.test_connection",
            new_callable=AsyncMock,
            return_value=(True, "连接成功", 8.0),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post("/resources/queues/queue-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] is True


class TestPubSubResourceRoutes:
    """发布订阅资源配置路由测试"""

    @pytest.fixture
    def mock_admin(self):
        return {"id": "admin-1", "username": "admin"}

    @pytest.fixture
    def mock_pubsub_config(self):
        config = MagicMock()
        config.id = "pubsub-1"
        config.name = "测试发布订阅"
        config.type = "kafka"
        config.host = "localhost"
        config.port = 9092
        config.username = None
        config.password = None
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        return config

    @pytest.mark.asyncio
    async def test_list_pubsub_configs_route_accessible(self, mock_admin, mock_pubsub_config):
        """测试 GET /resources/pubsubs 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.pubsub_config_service.PubSubConfigService.list_configs",
            new_callable=AsyncMock,
            return_value=([mock_pubsub_config], 1),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/resources/pubsubs")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_test_pubsub_connection_route_accessible(self, mock_admin):
        """测试 POST /resources/pubsubs/{id}/test-connection 路由可访问"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.pubsub_config_service.PubSubConfigService.test_connection",
            new_callable=AsyncMock,
            return_value=(True, "连接成功", 12.0),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post("/resources/pubsubs/pubsub-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] is True


class TestConnectionTestResult:
    """连通性测试结果测试"""

    @pytest.fixture
    def mock_admin(self):
        return {"id": "admin-1", "username": "admin"}

    @pytest.mark.asyncio
    async def test_connection_test_result_format(self, mock_admin):
        """测试连通性测试接口返回正确格式"""
        with patch(
            "tenant.controllers.admin.resource_controller.get_current_admin",
            return_value=mock_admin,
        ), patch(
            "tenant.services.database_config_service.DatabaseConfigService.test_connection",
            new_callable=AsyncMock,
            return_value=(False, "连接失败：超时", None),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post("/resources/databases/db-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data["data"]
        assert "message" in data["data"]
        assert "latency_ms" in data["data"]
        assert data["data"]["success"] is False
        assert "超时" in data["data"]["message"]
