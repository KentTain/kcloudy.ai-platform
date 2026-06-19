"""会话与消息模型集成测试 — 多租户隔离和 CRUD"""

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker

os.environ["PYTHON_SERVICE_ENV"] = "local"

from ai.models.conversation import Conversation
from ai.models.enums import (
    ConversationMode,
    ConversationStatus,
    MessageRole,
    MessageStatus,
)
from ai.models.message import Message


@pytest_asyncio.fixture(scope="module")
async def db_engine():
    from pathlib import Path

    from sqlalchemy.ext.asyncio import create_async_engine

    from framework.configs import init_settings

    config_dir = Path(__file__).parent.parent.parent.parent.parent / "config"
    settings = init_settings(config_dir)

    engine = create_async_engine(
        url=settings.sqlalchemy.url,
        echo=False,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """每个测试独立的数据库会话，测试后回滚"""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session, session.begin():
        yield session
        await session.rollback()


@pytest.fixture
def tenant_a_id():
    return str(uuid.uuid4())


@pytest.fixture
def tenant_b_id():
    return str(uuid.uuid4())


@pytest.fixture
def app_id():
    return str(uuid.uuid4())


class TestConversationCRUD:
    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session, tenant_a_id, app_id):
        conv = Conversation(
            tenant_id=tenant_a_id,
            app_id=app_id,
            name="测试会话",
            status=ConversationStatus.NORMAL,
            mode=ConversationMode.CHAT,
        )
        db_session.add(conv)
        await db_session.flush()

        assert conv.id is not None
        assert conv.tenant_id == tenant_a_id
        assert conv.name == "测试会话"
        assert conv.status == ConversationStatus.NORMAL

    @pytest.mark.asyncio
    async def test_conversation_status_transitions(self, db_session, tenant_a_id, app_id):
        conv = Conversation(
            tenant_id=tenant_a_id,
            app_id=app_id,
            name="状态测试",
            status=ConversationStatus.NORMAL,
            mode=ConversationMode.CHAT,
        )
        db_session.add(conv)
        await db_session.flush()

        # 归档
        conv.status = ConversationStatus.ARCHIVED
        await db_session.flush()
        assert conv.status == ConversationStatus.ARCHIVED

        # 软删除
        conv.status = ConversationStatus.DELETED
        await db_session.flush()
        assert conv.status == ConversationStatus.DELETED


class TestMessageCRUD:
    @pytest.mark.asyncio
    async def test_create_message(self, db_session, tenant_a_id, app_id):
        conv = Conversation(
            tenant_id=tenant_a_id,
            app_id=app_id,
            name="消息测试",
            status=ConversationStatus.NORMAL,
            mode=ConversationMode.CHAT,
        )
        db_session.add(conv)
        await db_session.flush()

        msg = Message(
            tenant_id=tenant_a_id,
            app_id=app_id,
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="你好",
            status=MessageStatus.PENDING,
            query="你好",
        )
        db_session.add(msg)
        await db_session.flush()

        assert msg.id is not None
        assert msg.conversation_id == conv.id
        assert msg.status == MessageStatus.PENDING

    @pytest.mark.asyncio
    async def test_message_status_transitions(self, db_session, tenant_a_id, app_id):
        conv = Conversation(
            tenant_id=tenant_a_id,
            app_id=app_id,
            name="消息状态测试",
            status=ConversationStatus.NORMAL,
            mode=ConversationMode.CHAT,
        )
        db_session.add(conv)
        await db_session.flush()

        msg = Message(
            tenant_id=tenant_a_id,
            app_id=app_id,
            conversation_id=conv.id,
            role=MessageRole.USER,
            status=MessageStatus.PENDING,
            query="测试",
        )
        db_session.add(msg)
        await db_session.flush()

        # 完成
        msg.status = MessageStatus.COMPLETED
        msg.answer = "回答内容"
        msg.token_count = 100
        await db_session.flush()
        assert msg.status == MessageStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_message_metadata_jsonb(self, db_session, tenant_a_id, app_id):
        conv = Conversation(
            tenant_id=tenant_a_id,
            app_id=app_id,
            name="元数据测试",
            status=ConversationStatus.NORMAL,
            mode=ConversationMode.CHAT,
        )
        db_session.add(conv)
        await db_session.flush()

        metadata = {"model": "gpt-4", "tokens": {"prompt": 50, "completion": 100}}
        msg = Message(
            tenant_id=tenant_a_id,
            app_id=app_id,
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            status=MessageStatus.COMPLETED,
            message_metadata=metadata,
        )
        db_session.add(msg)
        await db_session.flush()

        assert msg.message_metadata == metadata


class TestTenantIsolation:
    @pytest.mark.asyncio
    async def test_tenant_isolation(self, db_session, tenant_a_id, tenant_b_id, app_id):
        """不同租户的会话应该相互隔离"""
        conv_a = Conversation(
            tenant_id=tenant_a_id,
            app_id=app_id,
            name="租户A的会话",
            status=ConversationStatus.NORMAL,
            mode=ConversationMode.CHAT,
        )
        conv_b = Conversation(
            tenant_id=tenant_b_id,
            app_id=app_id,
            name="租户B的会话",
            status=ConversationStatus.NORMAL,
            mode=ConversationMode.CHAT,
        )
        db_session.add_all([conv_a, conv_b])
        await db_session.flush()

        # 查询租户 A 的会话
        from sqlalchemy import select
        result = await db_session.execute(
            select(Conversation).where(Conversation.tenant_id == tenant_a_id)
        )
        tenant_a_convs = result.scalars().all()
        assert len(tenant_a_convs) >= 1
        assert all(c.tenant_id == tenant_a_id for c in tenant_a_convs)

        # 查询租户 B 的会话
        result = await db_session.execute(
            select(Conversation).where(Conversation.tenant_id == tenant_b_id)
        )
        tenant_b_convs = result.scalars().all()
        assert len(tenant_b_convs) >= 1
        assert all(c.tenant_id == tenant_b_id for c in tenant_b_convs)

    @pytest.mark.asyncio
    async def test_message_tenant_isolation(self, db_session, tenant_a_id, tenant_b_id, app_id):
        """不同租户的消息应该相互隔离"""
        conv_a = Conversation(
            tenant_id=tenant_a_id,
            app_id=app_id,
            name="租户A",
            status=ConversationStatus.NORMAL,
            mode=ConversationMode.CHAT,
        )
        conv_b = Conversation(
            tenant_id=tenant_b_id,
            app_id=app_id,
            name="租户B",
            status=ConversationStatus.NORMAL,
            mode=ConversationMode.CHAT,
        )
        db_session.add_all([conv_a, conv_b])
        await db_session.flush()

        msg_a = Message(
            tenant_id=tenant_a_id,
            app_id=app_id,
            conversation_id=conv_a.id,
            role=MessageRole.USER,
            status=MessageStatus.PENDING,
            query="租户A的问题",
        )
        msg_b = Message(
            tenant_id=tenant_b_id,
            app_id=app_id,
            conversation_id=conv_b.id,
            role=MessageRole.USER,
            status=MessageStatus.PENDING,
            query="租户B的问题",
        )
        db_session.add_all([msg_a, msg_b])
        await db_session.flush()

        from sqlalchemy import select
        result = await db_session.execute(
            select(Message).where(Message.tenant_id == tenant_a_id)
        )
        tenant_a_msgs = result.scalars().all()
        assert all(m.tenant_id == tenant_a_id for m in tenant_a_msgs)
