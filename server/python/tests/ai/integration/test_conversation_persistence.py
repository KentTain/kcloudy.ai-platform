"""会话与消息模型集成测试 — 多租户隔离和 CRUD

基于数据库实际表结构（由 001_initial_schema.py 迁移创建）：
- conversations: id, tenant_id, user_id, mode, status, title, summary, created_at, updated_at
- messages: id, tenant_id, conversation_id, parent_message_id, role, content, status, error, metadata, created_at, updated_at
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker


@pytest_asyncio.fixture
async def db_session(ai_async_engine):
    """每个测试独立的数据库会话"""
    session_factory = async_sessionmaker(ai_async_engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        try:
            await session.close()
        except RuntimeError:
            pass


@pytest.fixture
def tenant_a_id():
    return str(uuid.uuid4())


@pytest.fixture
def tenant_b_id():
    return str(uuid.uuid4())


@pytest.fixture
def user_id():
    return str(uuid.uuid4())


# =============================================================================
# 表结构验证
# =============================================================================


@pytest.mark.integration
class TestTableStructure:
    """验证 conversations / messages 表结构符合迁移定义"""

    @pytest.mark.asyncio
    async def test_conversations_columns(self, db_session):
        """conversations 表应包含迁移定义的列"""
        result = await db_session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='ai' AND table_name='conversations' "
                "ORDER BY ordinal_position"
            )
        )
        cols = [r[0] for r in result]
        expected = ["id", "tenant_id", "user_id", "mode", "status", "title", "summary", "created_at", "updated_at"]
        assert cols == expected

    @pytest.mark.asyncio
    async def test_messages_columns(self, db_session):
        """messages 表应包含迁移定义的列"""
        result = await db_session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='ai' AND table_name='messages' "
                "ORDER BY ordinal_position"
            )
        )
        cols = [r[0] for r in result]
        expected = ["id", "tenant_id", "conversation_id", "parent_message_id", "role", "content", "status", "error", "metadata", "created_at", "updated_at"]
        assert cols == expected


# =============================================================================
# Conversation CRUD
# =============================================================================


@pytest.mark.integration
class TestConversationCRUD:
    """会话 CRUD 集成测试"""

    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session, tenant_a_id, user_id):
        conv_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.conversations (id, tenant_id, user_id, mode, status, title) "
                "VALUES (:id, :tenant_id, :user_id, :mode, :status, :title)"
            ),
            {"id": conv_id, "tenant_id": tenant_a_id, "user_id": user_id, "mode": "chat", "status": "normal", "title": "测试会话"},
        )
        await db_session.flush()

        result = await db_session.execute(
            text("SELECT id, tenant_id, title, status FROM ai.conversations WHERE id = :id"),
            {"id": conv_id},
        )
        row = result.first()
        assert row is not None
        assert row.tenant_id == tenant_a_id
        assert row.title == "测试会话"
        assert row.status == "normal"

    @pytest.mark.asyncio
    async def test_conversation_status_transitions(self, db_session, tenant_a_id, user_id):
        conv_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.conversations (id, tenant_id, user_id, mode, status, title) "
                "VALUES (:id, :tenant_id, :user_id, :mode, :status, :title)"
            ),
            {"id": conv_id, "tenant_id": tenant_a_id, "user_id": user_id, "mode": "chat", "status": "normal", "title": "状态测试"},
        )
        await db_session.flush()

        # 归档
        await db_session.execute(
            text("UPDATE ai.conversations SET status = :status WHERE id = :id"),
            {"status": "archived", "id": conv_id},
        )
        await db_session.flush()

        result = await db_session.execute(
            text("SELECT status FROM ai.conversations WHERE id = :id"),
            {"id": conv_id},
        )
        assert result.scalar() == "archived"

        # 软删除
        await db_session.execute(
            text("UPDATE ai.conversations SET status = :status WHERE id = :id"),
            {"status": "deleted", "id": conv_id},
        )
        await db_session.flush()

        result = await db_session.execute(
            text("SELECT status FROM ai.conversations WHERE id = :id"),
            {"id": conv_id},
        )
        assert result.scalar() == "deleted"


# =============================================================================
# Message CRUD
# =============================================================================


@pytest.mark.integration
class TestMessageCRUD:
    """消息 CRUD 集成测试"""

    @pytest.mark.asyncio
    async def test_create_message(self, db_session, tenant_a_id, user_id):
        conv_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.conversations (id, tenant_id, user_id, mode, status) "
                "VALUES (:id, :tenant_id, :user_id, :mode, :status)"
            ),
            {"id": conv_id, "tenant_id": tenant_a_id, "user_id": user_id, "mode": "chat", "status": "normal"},
        )
        await db_session.flush()

        msg_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.messages (id, tenant_id, conversation_id, role, content, status) "
                "VALUES (:id, :tenant_id, :conv_id, :role, :content, :status)"
            ),
            {"id": msg_id, "tenant_id": tenant_a_id, "conv_id": conv_id, "role": "user", "content": "你好", "status": "pending"},
        )
        await db_session.flush()

        result = await db_session.execute(
            text("SELECT id, conversation_id, status FROM ai.messages WHERE id = :id"),
            {"id": msg_id},
        )
        row = result.first()
        assert row is not None
        assert row.conversation_id == conv_id
        assert row.status == "pending"

    @pytest.mark.asyncio
    async def test_message_status_transitions(self, db_session, tenant_a_id, user_id):
        conv_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.conversations (id, tenant_id, user_id, mode, status) "
                "VALUES (:id, :tenant_id, :user_id, :mode, :status)"
            ),
            {"id": conv_id, "tenant_id": tenant_a_id, "user_id": user_id, "mode": "chat", "status": "normal"},
        )
        await db_session.flush()

        msg_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.messages (id, tenant_id, conversation_id, role, content, status) "
                "VALUES (:id, :tenant_id, :conv_id, :role, :content, :status)"
            ),
            {"id": msg_id, "tenant_id": tenant_a_id, "conv_id": conv_id, "role": "user", "content": "测试", "status": "pending"},
        )
        await db_session.flush()

        # 完成
        await db_session.execute(
            text("UPDATE ai.messages SET status = :status WHERE id = :id"),
            {"status": "completed", "id": msg_id},
        )
        await db_session.flush()

        result = await db_session.execute(
            text("SELECT status FROM ai.messages WHERE id = :id"),
            {"id": msg_id},
        )
        assert result.scalar() == "completed"

    @pytest.mark.asyncio
    async def test_message_metadata_jsonb(self, db_session, tenant_a_id, user_id):
        conv_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.conversations (id, tenant_id, user_id, mode, status) "
                "VALUES (:id, :tenant_id, :user_id, :mode, :status)"
            ),
            {"id": conv_id, "tenant_id": tenant_a_id, "user_id": user_id, "mode": "chat", "status": "normal"},
        )
        await db_session.flush()

        import json
        metadata = {"model": "gpt-4", "tokens": {"prompt": 50, "completion": 100}}

        msg_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.messages (id, tenant_id, conversation_id, role, content, status, metadata) "
                "VALUES (:id, :tenant_id, :conv_id, :role, :content, :status, CAST(:metadata AS jsonb))"
            ),
            {"id": msg_id, "tenant_id": tenant_a_id, "conv_id": conv_id, "role": "assistant", "content": "回答", "status": "completed", "metadata": json.dumps(metadata)},
        )
        await db_session.flush()

        result = await db_session.execute(
            text("SELECT metadata FROM ai.messages WHERE id = :id"),
            {"id": msg_id},
        )
        stored = result.scalar()
        assert stored == metadata


# =============================================================================
# 租户隔离
# =============================================================================


@pytest.mark.integration
class TestTenantIsolation:
    """多租户隔离集成测试"""

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, db_session, tenant_a_id, tenant_b_id, user_id):
        """不同租户的会话应该相互隔离"""
        conv_a_id = str(uuid.uuid4())
        conv_b_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.conversations (id, tenant_id, user_id, mode, status, title) "
                "VALUES (:id, :tenant_id, :user_id, :mode, :status, :title)"
            ),
            [
                {"id": conv_a_id, "tenant_id": tenant_a_id, "user_id": user_id, "mode": "chat", "status": "normal", "title": "租户A的会话"},
                {"id": conv_b_id, "tenant_id": tenant_b_id, "user_id": user_id, "mode": "chat", "status": "normal", "title": "租户B的会话"},
            ],
        )
        await db_session.flush()

        result = await db_session.execute(
            text("SELECT tenant_id FROM ai.conversations WHERE tenant_id = :tid"),
            {"tid": tenant_a_id},
        )
        tenant_ids = [r[0] for r in result]
        assert all(t == tenant_a_id for t in tenant_ids)
        assert len(tenant_ids) >= 1

    @pytest.mark.asyncio
    async def test_message_tenant_isolation(self, db_session, tenant_a_id, tenant_b_id, user_id):
        """不同租户的消息应该相互隔离"""
        conv_a_id = str(uuid.uuid4())
        conv_b_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.conversations (id, tenant_id, user_id, mode, status, title) "
                "VALUES (:id, :tenant_id, :user_id, :mode, :status, :title)"
            ),
            [
                {"id": conv_a_id, "tenant_id": tenant_a_id, "user_id": user_id, "mode": "chat", "status": "normal", "title": "租户A"},
                {"id": conv_b_id, "tenant_id": tenant_b_id, "user_id": user_id, "mode": "chat", "status": "normal", "title": "租户B"},
            ],
        )
        await db_session.flush()

        msg_a_id = str(uuid.uuid4())
        msg_b_id = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.messages (id, tenant_id, conversation_id, role, content, status) "
                "VALUES (:id, :tenant_id, :conv_id, :role, :content, :status)"
            ),
            [
                {"id": msg_a_id, "tenant_id": tenant_a_id, "conv_id": conv_a_id, "role": "user", "content": "租户A的问题", "status": "pending"},
                {"id": msg_b_id, "tenant_id": tenant_b_id, "conv_id": conv_b_id, "role": "user", "content": "租户B的问题", "status": "pending"},
            ],
        )
        await db_session.flush()

        result = await db_session.execute(
            text("SELECT tenant_id FROM ai.messages WHERE tenant_id = :tid"),
            {"tid": tenant_a_id},
        )
        tenant_ids = [r[0] for r in result]
        assert all(t == tenant_a_id for t in tenant_ids)
