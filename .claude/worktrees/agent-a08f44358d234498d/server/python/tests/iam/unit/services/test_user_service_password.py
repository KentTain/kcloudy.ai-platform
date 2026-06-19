"""
UserService 密码管理测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from iam.services.user_service import UserService


class TestChangePassword:
    """change_password 方法测试"""

    @pytest.mark.asyncio
    async def test_changes_password_and_invalidates_sessions(self):
        """修改密码后使所有会话失效"""
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.password_hash = "old_hash"

        with patch("iam.services.user_service.async_session") as mock_session, \
             patch("iam.services.user_service.verify_password", return_value=True), \
             patch("iam.services.user_service.hash_password", return_value="new_hash"), \
             patch("iam.services.user_service.delete_user_sessions", new_callable=AsyncMock) as mock_delete:

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session_context.execute.return_value = mock_result

            mock_delete.return_value = 3  # 删除了 3 个会话

            result = await UserService.change_password(
                user_id="user-1",
                old_password="old_pass",
                new_password="NewPass123!",
            )

        assert result is True
        mock_delete.assert_awaited_once_with("user-1")

    @pytest.mark.asyncio
    async def test_raises_error_for_wrong_old_password(self):
        """原密码错误时抛出异常"""
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.password_hash = "old_hash"

        with patch("iam.services.user_service.async_session") as mock_session, \
             patch("iam.services.user_service.verify_password", return_value=False):

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session_context.execute.return_value = mock_result

            with pytest.raises(ValueError) as exc:
                await UserService.change_password(
                    user_id="user-1",
                    old_password="wrong_pass",
                    new_password="NewPass123!",
                )

            assert "原密码错误" in str(exc.value)


class TestResetPassword:
    """reset_password 方法测试"""

    @pytest.mark.asyncio
    async def test_resets_password_and_invalidates_sessions(self):
        """重置密码后使所有会话失效"""
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.username = "testuser"

        with patch("iam.services.user_service.async_session") as mock_session, \
             patch("iam.services.user_service.hash_password", return_value="new_hash"), \
             patch("iam.services.user_service.delete_user_sessions", new_callable=AsyncMock) as mock_delete:

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session_context.execute.return_value = mock_result

            result = await UserService.reset_password(
                email="test@example.com",
                code="123456",
                new_password="NewPass123!",
            )

        assert result is True
        mock_delete.assert_awaited_once_with("user-1")


class TestAdminResetPassword:
    """admin_reset_password 方法测试"""

    @pytest.mark.asyncio
    async def test_generates_random_password_when_not_provided(self):
        """未提供密码时生成随机密码"""
        mock_user = MagicMock()
        mock_user.id = "user-1"

        with patch("iam.services.user_service.async_session") as mock_session, \
             patch("iam.services.user_service.hash_password", return_value="hashed"), \
             patch("iam.services.user_service.delete_user_sessions", new_callable=AsyncMock) as mock_delete:

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session_context.execute.return_value = mock_result

            password = await UserService.admin_reset_password(user_id="user-1")

        assert password is not None
        assert len(password) == 12  # 随机密码长度
        mock_delete.assert_awaited_once_with("user-1")

    @pytest.mark.asyncio
    async def test_uses_provided_password(self):
        """使用提供的密码"""
        mock_user = MagicMock()
        mock_user.id = "user-1"

        with patch("iam.services.user_service.async_session") as mock_session, \
             patch("iam.services.user_service.validate_password_strength"), \
             patch("iam.services.user_service.hash_password", return_value="hashed"), \
             patch("iam.services.user_service.delete_user_sessions", new_callable=AsyncMock) as mock_delete:

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session_context.execute.return_value = mock_result

            password = await UserService.admin_reset_password(
                user_id="user-1",
                new_password="CustomPass123!",
            )

        assert password == "CustomPass123!"
        mock_delete.assert_awaited_once_with("user-1")
