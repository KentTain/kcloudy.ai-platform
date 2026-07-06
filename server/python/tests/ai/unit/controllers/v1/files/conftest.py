# tests/ai/unit/controllers/v1/files/conftest.py
import pytest
import pytest_asyncio
from datetime import datetime
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.tenant.context import TenantContext
from iam.dependencies import get_current_user_id


class _MockSession:
    """模拟数据库会话"""

    def __init__(self):
        self.added_objects = []

    def add(self, obj):
        self.added_objects.append(obj)

    async def commit(self):
        pass

    async def flush(self):
        pass

    async def refresh(self, obj):
        pass

    async def execute(self, query):
        class _MockResult:
            def scalar_one_or_none(self):
                return None

            def one(self):
                class _MockRow:
                    total_messages = 0
                    total_tokens = None
                    avg_response_time = None

                return _MockRow()

            def scalars(self):
                class _MockScalars:
                    def all(self):
                        return []

                return _MockScalars()

        return _MockResult()

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration

    async def refresh_and_set_defaults(self, obj):
        now = datetime.now()
        if hasattr(obj, "created_at") and obj.created_at is None:
            obj.created_at = now

    async def rollback(self):
        pass

    async def close(self):
        pass


@pytest_asyncio.fixture
async def client():
    """创建测试用的 HTTP 客户端"""
    from ai.controllers.v1.files import router as files_router

    app = FastAPI()
    app.include_router(files_router, prefix="/ai/console/v1")

    mock_session = _MockSession()

    async def override_get_db_session():
        yield mock_session

    # Mock Redis client
    class _MockRedis:
        def __init__(self):
            self._store = {}

        async def sadd(self, key, value):
            if key not in self._store:
                self._store[key] = set()
            self._store[key].add(str(value))

        async def expire(self, key, seconds):
            pass

        async def smembers(self, key):
            return self._store.get(key, set())

        async def delete(self, key):
            if key in self._store:
                del self._store[key]

    mock_redis = _MockRedis()

    async def override_get_redis_client():
        return mock_redis

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user_id] = lambda: "test-user-001"

    from framework.cache.dependencies import get_redis_client
    app.dependency_overrides[get_redis_client] = override_get_redis_client

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        TenantContext.set_tenant_id("test-tenant-001")
        yield ac
        TenantContext.clear()
