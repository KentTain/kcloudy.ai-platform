"""
metadata 控制器测试配置

提供测试用的 AsyncClient 客户端 fixture。
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from framework.database.dependencies import get_db_session
from framework.tenant.context import TenantContext
from iam.dependencies import get_current_user_id


class _MockSession:
    """模拟数据库会话"""

    def __init__(self):
        self.added_objects = []
        self.committed = False
        self._records: dict[str, dict] = {}

    def _make_record_mock(self, record: dict):
        """从记录 dict 创建 mock 对象"""
        obj = MagicMock()
        obj.message_id = record["message_id"]
        obj.tenant_id = record.get("tenant_id", "test-tenant-001")
        obj.user_id = record.get("user_id", "test-user-001")
        obj.rating = record.get("rating")
        obj.feedback = record.get("feedback")
        obj.created_at = record.get("created_at", datetime.now())
        obj.updated_at = record.get("updated_at")
        return obj

    async def execute(self, query):
        """模拟 SQLAlchemy session.execute()"""
        # 从语句中提取 message_id 绑定参数
        message_id = None
        try:
            compiled = query.compile(compile_kwargs={"literal_binds": True})
            compiled_str = str(compiled)
            if compiled_str:
                for part in compiled_str.split():
                    if part.startswith("'msg-"):
                        message_id = part.strip("'")
                        break
        except Exception:
            pass

        if message_id and message_id in self._records:
            record = self._records[message_id]
            return MagicMock(
                scalar_one_or_none=MagicMock(
                    return_value=self._make_record_mock(record)
                )
            )

        return MagicMock(scalar_one_or_none=MagicMock(return_value=None))

    def add(self, obj):
        self.added_objects.append(obj)
        self._records[obj.message_id] = {
            "message_id": obj.message_id,
            "tenant_id": obj.tenant_id,
            "user_id": obj.user_id,
            "rating": obj.rating,
            "feedback": obj.feedback,
        }

    async def commit(self):
        self.committed = True
        now = datetime.now()
        for obj in self.added_objects:
            if hasattr(obj, "created_at") and obj.created_at is None:
                obj.created_at = now
            # 同步 mock 对象的 rating/feedback 变更到存储
            mid = obj.message_id
            if mid in self._records:
                self._records[mid]["rating"] = obj.rating
                self._records[mid]["feedback"] = obj.feedback

    async def refresh(self, obj):
        """模拟 SQLAlchemy session.refresh()"""
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
    from ai.controllers.v1.metadata import router as metadata_router

    app = FastAPI()
    app.include_router(metadata_router, prefix="/ai/console/v1")

    mock_session = _MockSession()

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user_id] = lambda: "test-user-001"

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        TenantContext.set_tenant_id("test-tenant-001")
        yield ac
        TenantContext.clear()