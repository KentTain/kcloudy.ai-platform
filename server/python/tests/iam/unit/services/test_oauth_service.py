"""
OAuthService 测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from iam.services.oauth_service import OAuthService


class TestBindOAuth:
    """bind_oauth 方法测试"""

    @pytest.mark.asyncio
    async def test_binds_oauth_to_user(self, session):
        """成功绑定 OAuth 账号"""
        # 第一次查询：检查 OAuth 是否已被绑定（返回 None）
        # 第二次查询：检查用户是否已绑定该类型 OAuth（返回 None）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [None, None]
        session.execute.return_value = mock_result

        result = await OAuthService.bind_oauth(
            session,
            user_id="user-1",
            provider="wechat",
            code="auth_code_123",
        )

        assert result is not None
        assert result.user_id == "user-1"
        assert result.provider == "wechat"

    @pytest.mark.asyncio
    async def test_raises_error_when_already_bound_to_same_user(self, session):
        """已绑定到当前用户时抛出异常"""
        mock_conn = MagicMock()
        mock_conn.user_id = "user-1"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conn
        session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc:
            await OAuthService.bind_oauth(
                session,
                user_id="user-1",
                provider="wechat",
                code="auth_code_123",
            )

        assert "已绑定到当前用户" in str(exc.value)

    @pytest.mark.asyncio
    async def test_raises_error_when_already_bound_to_other_user(self, session):
        """已被其他用户绑定时抛出异常"""
        mock_conn = MagicMock()
        mock_conn.user_id = "user-2"  # 其他用户

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conn
        session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc:
            await OAuthService.bind_oauth(
                session,
                user_id="user-1",
                provider="wechat",
                code="auth_code_123",
            )

        assert "已被其他用户绑定" in str(exc.value)

    @pytest.mark.asyncio
    async def test_raises_error_when_user_already_has_this_provider(self, session):
        """用户已绑定该类型 OAuth 时抛出异常"""
        mock_existing = MagicMock()

        mock_result = MagicMock()
        # 第一次查询：OAuth 未被绑定（返回 None）
        # 第二次查询：用户已绑定该类型（返回 existing）
        mock_result.scalar_one_or_none.side_effect = [None, mock_existing]
        session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc:
            await OAuthService.bind_oauth(
                session,
                user_id="user-1",
                provider="wechat",
                code="auth_code_123",
            )

        assert "已绑定过" in str(exc.value)


class TestUnbindOAuth:
    """unbind_oauth 方法测试"""

    @pytest.mark.asyncio
    async def test_unbinds_oauth_successfully(self, session):
        """成功解绑 OAuth 账号"""
        mock_user = MagicMock()
        mock_user.password_hash = "hashed_password"

        mock_conn = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_user, mock_conn]
        session.execute.return_value = mock_result

        result = await OAuthService.unbind_oauth(
            session,
            user_id="user-1",
            provider="wechat",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_raises_error_when_no_password(self, session):
        """用户未设置密码时抛出异常"""
        mock_user = MagicMock()
        mock_user.password_hash = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc:
            await OAuthService.unbind_oauth(
                session,
                user_id="user-1",
                provider="wechat",
            )

        assert "请先设置密码" in str(exc.value)

    @pytest.mark.asyncio
    async def test_raises_error_when_not_bound(self, session):
        """未绑定该类型账号时抛出异常"""
        mock_user = MagicMock()
        mock_user.password_hash = "hashed_password"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_user, None]
        session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc:
            await OAuthService.unbind_oauth(
                session,
                user_id="user-1",
                provider="wechat",
            )

        assert "未绑定" in str(exc.value)


class TestGetUserOAuthConnections:
    """get_user_oauth_connections 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_user_connections(self, session):
        """返回用户的 OAuth 关联列表"""
        mock_conn1 = MagicMock()
        mock_conn1.provider = "wechat"
        mock_conn2 = MagicMock()
        mock_conn2.provider = "wework"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_conn1, mock_conn2]
        session.execute.return_value = mock_result

        connections = await OAuthService.get_user_oauth_connections(session, "user-1")

        assert len(connections) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_connections(self, session):
        """用户无 OAuth 关联时返回空列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result

        connections = await OAuthService.get_user_oauth_connections(session, "user-1")

        assert connections == []
