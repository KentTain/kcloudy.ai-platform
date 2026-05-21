"""
session 模块单元测试

测试 Redis 会话管理功能（使用 mock）
"""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCreateSession:
    """创建会话测试"""

    @pytest.mark.asyncio
    async def test_create_session_success(self):
        """
        场景：创建会话成功
        WHEN: 提供有效用户信息
        THEN: 返回 session_id 并存储会话到 Redis
        """
        from framework.utils import session as session_module

        # 创建 AsyncMock
        mock_set = AsyncMock(return_value=True)

        with patch.object(session_module.RedisUtil, "set", mock_set):
            session_id = await session_module.create_session(
                user_id="user-123",
                tenant_id="tenant-456",
                device_info="Chrome/Windows",
                ip="192.168.1.1",
            )

            assert session_id is not None
            assert len(session_id) > 10
            # 验证 set 被调用
            mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_with_ttl(self):
        """
        场景：创建会话并设置 TTL
        WHEN: 指定过期时间
        THEN: 会话在 Redis 中有过期时间
        """
        from framework.utils import session as session_module

        mock_set = AsyncMock(return_value=True)

        with patch.object(session_module.RedisUtil, "set", mock_set):
            session_id = await session_module.create_session(
                user_id="user-123",
                tenant_id="tenant-456",
                ttl=timedelta(days=7),
            )

            assert session_id is not None
            # 验证 TTL 被传递
            call_args = mock_set.call_args
            assert call_args is not None
            # 第三个参数是 ttl
            assert "ttl" in call_args.kwargs or len(call_args.args) >= 3


class TestGetSession:
    """获取会话测试"""

    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """
        场景：获取存在的会话
        WHEN: 提供 session_id
        THEN: 返回会话数据
        """
        from framework.utils import session as session_module

        session_data = (
            '{"user_id": "user-123", "tenant_id": "tenant-456", "version": 1}'
        )
        mock_get = AsyncMock(return_value=session_data)

        with patch.object(session_module.RedisUtil, "get", mock_get):
            session = await session_module.get_session("session-123")

            assert session is not None
            assert session["user_id"] == "user-123"
            assert session["tenant_id"] == "tenant-456"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """
        场景：获取不存在的会话
        WHEN: session_id 无效
        THEN: 返回 None
        """
        from framework.utils import session as session_module

        mock_get = AsyncMock(return_value=None)

        with patch.object(session_module.RedisUtil, "get", mock_get):
            session = await session_module.get_session("nonexistent-session")

            assert session is None


class TestDeleteSession:
    """删除会话测试"""

    @pytest.mark.asyncio
    async def test_delete_session_success(self):
        """
        场景：删除会话成功
        WHEN: 提供 session_id
        THEN: 会话被删除
        """
        from framework.utils import session as session_module

        mock_delete = AsyncMock(return_value=1)

        with patch.object(session_module.RedisUtil, "delete", mock_delete):
            await session_module.delete_session("session-123")

            mock_delete.assert_called_once()


class TestTokenBlacklist:
    """Token 黑名单测试"""

    @pytest.mark.asyncio
    async def test_add_to_blacklist(self):
        """
        场景：添加 Token 到黑名单
        WHEN: 调用 add_to_blacklist
        THEN: Token 被标记为无效
        """
        from framework.utils import session as session_module

        mock_set = AsyncMock(return_value=True)

        with patch.object(session_module.RedisUtil, "set", mock_set):
            await session_module.add_to_blacklist("token-jti-123", ttl_seconds=3600)

            mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_blacklisted_true(self):
        """
        场景：Token 在黑名单中
        WHEN: 检查已加入黑名单的 Token
        THEN: 返回 True
        """
        from framework.utils import session as session_module

        mock_exists = AsyncMock(return_value=True)

        with patch.object(session_module.RedisUtil, "exists", mock_exists):
            result = await session_module.is_blacklisted("token-jti-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_is_blacklisted_false(self):
        """
        场景：Token 未在黑名单
        WHEN: 检查未被加入黑名单的 Token
        THEN: 返回 False
        """
        from framework.utils import session as session_module

        mock_exists = AsyncMock(return_value=False)

        with patch.object(session_module.RedisUtil, "exists", mock_exists):
            result = await session_module.is_blacklisted("not-blacklisted-token")

            assert result is False


class TestUpdateSessionVersion:
    """更新会话版本测试"""

    @pytest.mark.asyncio
    async def test_update_version(self):
        """
        场景：更新会话版本
        WHEN: 调用 update_session_version
        THEN: 版本号增加
        """
        from framework.utils import session as session_module

        session_data = (
            '{"user_id": "user-123", "tenant_id": "tenant-456", "version": 1}'
        )
        mock_get = AsyncMock(return_value=session_data)
        mock_set = AsyncMock(return_value=True)

        with patch.object(session_module.RedisUtil, "get", mock_get):
            with patch.object(session_module.RedisUtil, "set", mock_set):
                await session_module.update_session_version("session-123")

                # 验证 set 被调用来更新会话
                mock_set.assert_called_once()


class TestSessionKeyFormat:
    """会话 Key 格式测试"""

    def test_session_key_format(self):
        """
        场景：会话 Key 格式正确
        WHEN: 生成会话 Key
        THEN: 格式为 session:{session_id}
        """
        from framework.utils.session import get_session_key

        key = get_session_key("session-123")
        assert key == "session:session-123"

    def test_session_key_with_prefix(self):
        """
        场景：带前缀的会话 Key
        WHEN: 指定 key_prefix
        THEN: Key 包含前缀
        """
        from framework.utils.session import get_session_key

        key = get_session_key("session-123", key_prefix="test:")
        assert key == "test:session:session-123"

    def test_blacklist_key_format(self):
        """
        场景：黑名单 Key 格式正确
        WHEN: 生成黑名单 Key
        THEN: 格式为 blacklist:{jti}
        """
        from framework.utils.session import get_blacklist_key

        key = get_blacklist_key("token-jti-123")
        assert key == "blacklist:token-jti-123"
