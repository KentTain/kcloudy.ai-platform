"""
会话管理工具测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from framework.utils.session import (
    delete_user_sessions,
    create_session,
    get_session,
    delete_session,
    _memory_sessions,
)


class TestDeleteUserSessions:
    """delete_user_sessions 测试"""

    @pytest.mark.asyncio
    async def test_deletes_all_sessions_for_user_in_redis(self):
        """Redis 模式下删除用户所有会话"""
        mock_redis = MagicMock()
        mock_redis.keys = AsyncMock(return_value=[
            "session:sess-1",
            "session:sess-2",
            "session:sess-3",
        ])
        mock_redis.get = AsyncMock(side_effect=[
            '{"user_id": "user-1", "tenant_id": "t1"}',
            '{"user_id": "user-2", "tenant_id": "t2"}',
            '{"user_id": "user-1", "tenant_id": "t1"}',
        ])
        mock_redis.delete = AsyncMock(return_value=1)

        with patch("framework.utils.session.RedisUtil") as redis_util:
            redis_util._client = mock_redis
            redis_util.keys = AsyncMock(return_value=["session:sess-1", "session:sess-2", "session:sess-3"])
            redis_util.get = AsyncMock(side_effect=[
                '{"user_id": "user-1", "tenant_id": "t1"}',
                '{"user_id": "user-2", "tenant_id": "t2"}',
                '{"user_id": "user-1", "tenant_id": "t1"}',
            ])
            redis_util.delete = AsyncMock(return_value=1)

            count = await delete_user_sessions("user-1")

        assert count == 2  # sess-1 和 sess-3 属于 user-1

    @pytest.mark.asyncio
    async def test_deletes_sessions_in_memory_mode(self):
        """内存模式下删除用户所有会话"""
        # 清空并设置内存会话
        _memory_sessions.clear()
        _memory_sessions["sess-1"] = {"user_id": "user-1", "tenant_id": "t1"}
        _memory_sessions["sess-2"] = {"user_id": "user-2", "tenant_id": "t2"}
        _memory_sessions["sess-3"] = {"user_id": "user-1", "tenant_id": "t1"}

        with patch("framework.utils.session._is_redis_available", return_value=False):
            count = await delete_user_sessions("user-1")

        assert count == 2
        assert "sess-1" not in _memory_sessions
        assert "sess-3" not in _memory_sessions
        assert "sess-2" in _memory_sessions

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_sessions(self):
        """用户无会话时返回 0"""
        _memory_sessions.clear()

        with patch("framework.utils.session._is_redis_available", return_value=False):
            count = await delete_user_sessions("user-no-sessions")

        assert count == 0


class TestCreateAndGetSession:
    """create_session 和 get_session 测试"""

    @pytest.mark.asyncio
    async def test_creates_session_in_memory_mode(self):
        """内存模式下创建会话"""
        _memory_sessions.clear()

        with patch("framework.utils.session._is_redis_available", return_value=False):
            session_id = await create_session(
                user_id="user-1",
                tenant_id="tenant-1",
                ip="127.0.0.1",
            )

        assert session_id is not None
        assert len(session_id) == 21  # nanoid 默认长度
        assert _memory_sessions[session_id]["user_id"] == "user-1"

    @pytest.mark.asyncio
    async def test_gets_session_in_memory_mode(self):
        """内存模式下获取会话"""
        _memory_sessions.clear()
        _memory_sessions["test-sess"] = {"user_id": "user-1", "tenant_id": "t1"}

        with patch("framework.utils.session._is_redis_available", return_value=False):
            session = await get_session("test-sess")

        assert session["user_id"] == "user-1"

    @pytest.mark.asyncio
    async def test_returns_none_for_nonexistent_session(self):
        """获取不存在的会话返回 None"""
        with patch("framework.utils.session._is_redis_available", return_value=False):
            session = await get_session("nonexistent")

        assert session is None


class TestDeleteSession:
    """delete_session 测试"""

    @pytest.mark.asyncio
    async def test_deletes_session_in_memory_mode(self):
        """内存模式下删除会话"""
        _memory_sessions.clear()
        _memory_sessions["sess-to-delete"] = {"user_id": "user-1"}

        with patch("framework.utils.session._is_redis_available", return_value=False):
            await delete_session("sess-to-delete")

        assert "sess-to-delete" not in _memory_sessions
