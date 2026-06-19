"""
资源配置 API 路由集成测试

测试 /resources/* 路由的 CRUD 操作和连通性测试接口。
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from framework.database.dependencies import get_db_session
from tenant.controllers.admin.resource_controller import router
from tenant.middlewares.admin_auth_middleware import get_current_admin

# 创建测试应用
app = FastAPI()
app.include_router(router)


# Mock 管理员数据
MOCK_ADMIN = {"id": "admin-1", "username": "admin"}


# Mock 数据库会话
@pytest.fixture
def mock_session():
    """模拟数据库会话"""
    return MagicMock()


# 覆盖依赖
@pytest.fixture(autouse=True)
def override_dependencies(mock_session):
    """自动覆盖 FastAPI 依赖"""
    # 覆盖 get_current_admin 依赖
    async def mock_get_current_admin():
        return MOCK_ADMIN

    # 覆盖 get_db_session 依赖
    async def mock_get_db_session():
        yield mock_session

    app.dependency_overrides[get_current_admin] = mock_get_current_admin
    app.dependency_overrides[get_db_session] = mock_get_db_session

    yield

    # 清理
    app.dependency_overrides.clear()


class TestDatabaseResourceRoutes:
    """数据库资源配置路由测试"""

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
        config.is_default = False
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        return config

    @pytest.fixture
    def mock_db_response(self):
        """模拟数据库配置响应"""
        return {
            "id": "db-1",
            "name": "测试数据库",
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "username": "admin",
            "password": "******",
            "is_default": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

    def test_list_database_configs_route_accessible(self, mock_db_config, mock_db_response, mock_session):
        """测试 GET /resources/databases 路由可访问"""
        with patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "list_configs",
            new_callable=AsyncMock,
            return_value=([mock_db_config], 1),
        ), patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "build_response",
            return_value=mock_db_response,
        ):
            client = TestClient(app)
            response = client.get("/resources/databases")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert data["total"] == 1

    def test_create_database_config_route_accessible(self, mock_db_config, mock_db_response, mock_session):
        """测试 POST /resources/databases 路由可访问"""
        with patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "create",
            new_callable=AsyncMock,
            return_value=mock_db_config,
        ), patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "build_response",
            return_value=mock_db_response,
        ):
            client = TestClient(app)
            response = client.post(
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

    def test_get_database_config_by_id_route_accessible(self, mock_db_config, mock_db_response, mock_session):
        """测试 GET /resources/databases/{id} 路由可访问"""
        with patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "get_by_id",
            new_callable=AsyncMock,
            return_value=mock_db_config,
        ), patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "build_response",
            return_value=mock_db_response,
        ):
            client = TestClient(app)
            response = client.get("/resources/databases/db-1")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == "db-1"

    def test_update_database_config_route_accessible(self, mock_db_config, mock_session):
        """测试 PUT /resources/databases/{id} 路由可访问"""
        updated_response = {
            "id": "db-1",
            "name": "更新后的数据库",
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "username": "admin",
            "password": "******",
            "is_default": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        with patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "update",
            new_callable=AsyncMock,
            return_value=mock_db_config,
        ), patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "build_response",
            return_value=updated_response,
        ):
            client = TestClient(app)
            response = client.put(
                "/resources/databases/db-1", json={"name": "更新后的数据库"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_delete_database_config_route_accessible(self, mock_session):
        """测试 DELETE /resources/databases/{id} 路由可访问"""
        with patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "delete",
            new_callable=AsyncMock,
            return_value=True,
        ):
            client = TestClient(app)
            response = client.delete("/resources/databases/db-1")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_test_database_connection_route_accessible(self, mock_session):
        """测试 POST /resources/databases/{id}/test-connection 路由可访问"""
        with patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "test_connection",
            new_callable=AsyncMock,
            return_value=(True, "连接成功", 10),  # latency_ms 是整数
        ):
            client = TestClient(app)
            response = client.post("/resources/databases/db-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["success"] is True
        assert data["data"]["latency_ms"] == 10

    def test_get_database_config_not_found(self, mock_session):
        """测试 GET /resources/databases/{id} 配置不存在返回 404"""
        with patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            client = TestClient(app)
            response = client.get("/resources/databases/nonexistent")

        assert response.status_code == 404


class TestStorageResourceRoutes:
    """存储资源配置路由测试"""

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
        config.is_default = False
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        return config

    @pytest.fixture
    def mock_storage_response(self):
        return {
            "id": "storage-1",
            "name": "测试存储",
            "type": "minio",
            "bucket": "test-bucket",
            "endpoint": "http://localhost:9000",
            "access_key": "admin",
            "secret_key": "******",
            "is_default": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

    def test_list_storage_configs_route_accessible(self, mock_storage_config, mock_storage_response, mock_session):
        """测试 GET /resources/storages 路由可访问"""
        with patch.object(
            __import__("tenant.services.storage_config_service", fromlist=["StorageConfigService"]).StorageConfigService,
            "list_configs",
            new_callable=AsyncMock,
            return_value=([mock_storage_config], 1),
        ), patch.object(
            __import__("tenant.services.storage_config_service", fromlist=["StorageConfigService"]).StorageConfigService,
            "build_response",
            return_value=mock_storage_response,
        ):
            client = TestClient(app)
            response = client.get("/resources/storages")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data

    def test_test_storage_connection_route_accessible(self, mock_session):
        """测试 POST /resources/storages/{id}/test-connection 路由可访问"""
        with patch.object(
            __import__("tenant.services.storage_config_service", fromlist=["StorageConfigService"]).StorageConfigService,
            "test_connection",
            new_callable=AsyncMock,
            return_value=(True, "连接成功", 15),  # latency_ms 是整数
        ):
            client = TestClient(app)
            response = client.post("/resources/storages/storage-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] is True


class TestCacheResourceRoutes:
    """缓存资源配置路由测试"""

    @pytest.fixture
    def mock_cache_config(self):
        config = MagicMock()
        config.id = "cache-1"
        config.name = "测试缓存"
        config.host = "localhost"
        config.port = 6379
        config.password = "******"
        config.db = 0
        config.prefix = None
        config.is_default = False
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        return config

    @pytest.fixture
    def mock_cache_response(self):
        return {
            "id": "cache-1",
            "name": "测试缓存",
            "host": "localhost",
            "port": 6379,
            "password": "******",
            "db": 0,
            "prefix": None,
            "is_default": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

    def test_list_cache_configs_route_accessible(self, mock_cache_config, mock_cache_response, mock_session):
        """测试 GET /resources/caches 路由可访问"""
        with patch.object(
            __import__("tenant.services.cache_config_service", fromlist=["CacheConfigService"]).CacheConfigService,
            "list_configs",
            new_callable=AsyncMock,
            return_value=([mock_cache_config], 1),
        ), patch.object(
            __import__("tenant.services.cache_config_service", fromlist=["CacheConfigService"]).CacheConfigService,
            "build_response",
            return_value=mock_cache_response,
        ):
            client = TestClient(app)
            response = client.get("/resources/caches")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_test_cache_connection_route_accessible(self, mock_session):
        """测试 POST /resources/caches/{id}/test-connection 路由可访问"""
        with patch.object(
            __import__("tenant.services.cache_config_service", fromlist=["CacheConfigService"]).CacheConfigService,
            "test_connection",
            new_callable=AsyncMock,
            return_value=(True, "连接成功", 5),  # latency_ms 是整数
        ):
            client = TestClient(app)
            response = client.post("/resources/caches/cache-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] is True


class TestQueueResourceRoutes:
    """队列资源配置路由测试"""

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
        config.is_default = False
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        return config

    @pytest.fixture
    def mock_queue_response(self):
        return {
            "id": "queue-1",
            "name": "测试队列",
            "type": "rabbitmq",
            "host": "localhost",
            "port": 5672,
            "username": "admin",
            "password": "******",
            "vhost": "/",
            "is_default": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

    def test_list_queue_configs_route_accessible(self, mock_queue_config, mock_queue_response, mock_session):
        """测试 GET /resources/queues 路由可访问"""
        with patch.object(
            __import__("tenant.services.queue_config_service", fromlist=["QueueConfigService"]).QueueConfigService,
            "list_configs",
            new_callable=AsyncMock,
            return_value=([mock_queue_config], 1),
        ), patch.object(
            __import__("tenant.services.queue_config_service", fromlist=["QueueConfigService"]).QueueConfigService,
            "build_response",
            return_value=mock_queue_response,
        ):
            client = TestClient(app)
            response = client.get("/resources/queues")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_test_queue_connection_route_accessible(self, mock_session):
        """测试 POST /resources/queues/{id}/test-connection 路由可访问"""
        with patch.object(
            __import__("tenant.services.queue_config_service", fromlist=["QueueConfigService"]).QueueConfigService,
            "test_connection",
            new_callable=AsyncMock,
            return_value=(True, "连接成功", 8),  # latency_ms 是整数
        ):
            client = TestClient(app)
            response = client.post("/resources/queues/queue-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] is True


class TestPubSubResourceRoutes:
    """发布订阅资源配置路由测试"""

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
        config.is_default = False
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        return config

    @pytest.fixture
    def mock_pubsub_response(self):
        return {
            "id": "pubsub-1",
            "name": "测试发布订阅",
            "type": "kafka",
            "host": "localhost",
            "port": 9092,
            "username": None,
            "password": None,
            "is_default": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

    def test_list_pubsub_configs_route_accessible(self, mock_pubsub_config, mock_pubsub_response, mock_session):
        """测试 GET /resources/pubsubs 路由可访问"""
        with patch.object(
            __import__("tenant.services.pubsub_config_service", fromlist=["PubSubConfigService"]).PubSubConfigService,
            "list_configs",
            new_callable=AsyncMock,
            return_value=([mock_pubsub_config], 1),
        ), patch.object(
            __import__("tenant.services.pubsub_config_service", fromlist=["PubSubConfigService"]).PubSubConfigService,
            "build_response",
            return_value=mock_pubsub_response,
        ):
            client = TestClient(app)
            response = client.get("/resources/pubsubs")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_test_pubsub_connection_route_accessible(self, mock_session):
        """测试 POST /resources/pubsubs/{id}/test-connection 路由可访问"""
        with patch.object(
            __import__("tenant.services.pubsub_config_service", fromlist=["PubSubConfigService"]).PubSubConfigService,
            "test_connection",
            new_callable=AsyncMock,
            return_value=(True, "连接成功", 12),  # latency_ms 是整数
        ):
            client = TestClient(app)
            response = client.post("/resources/pubsubs/pubsub-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] is True


class TestConnectionTestResult:
    """连通性测试结果测试"""

    def test_connection_test_result_format(self, mock_session):
        """测试连通性测试接口返回正确格式"""
        with patch.object(
            __import__("tenant.services.database_config_service", fromlist=["DatabaseConfigService"]).DatabaseConfigService,
            "test_connection",
            new_callable=AsyncMock,
            return_value=(False, "连接失败：超时", None),
        ):
            client = TestClient(app)
            response = client.post("/resources/databases/db-1/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data["data"]
        assert "message" in data["data"]
        assert "latency_ms" in data["data"]
        assert data["data"]["success"] is False
        assert "超时" in data["data"]["message"]
