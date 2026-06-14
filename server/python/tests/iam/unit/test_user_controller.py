"""用户控制器测试 - /me 接口返回角色权限"""

import json

import pytest
from fastapi import HTTPException
from fastapi.responses import ORJSONResponse
from unittest.mock import AsyncMock, patch, MagicMock

from iam.controllers.user_controller import get_current_user


@pytest.mark.asyncio
async def test_get_current_user_returns_roles_and_permissions():
    """get_current_user 应返回用户的角色和权限"""

    # Mock user
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.tenant_id = "tenant-123"
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.phone = None
    mock_user.nickname = "Test"
    mock_user.avatar = None
    mock_user.status = "active"
    mock_user.profile_completed = True
    mock_user.is_email_verified = False
    mock_user.is_phone_verified = False
    mock_user.last_login_at = None
    mock_user.created_at = "2024-01-01T00:00:00Z"

    # Mock roles
    mock_role_admin = MagicMock()
    mock_role_admin.code = "admin"
    mock_role_viewer = MagicMock()
    mock_role_viewer.code = "viewer"

    # Mock services
    with patch("iam.controllers.user_controller.user_service.get_by_id", new_callable=AsyncMock) as mock_get_user:
        with patch("iam.controllers.user_controller.user_roles_service.get_user_roles", new_callable=AsyncMock) as mock_get_roles:
            with patch("iam.controllers.user_controller.permission_check_service.get_user_permissions", new_callable=AsyncMock) as mock_get_perms:
                mock_get_user.return_value = mock_user
                mock_get_roles.return_value = [mock_role_admin, mock_role_viewer]
                mock_get_perms.return_value = ["iam:user:read", "iam:role:read"]

                result = await get_current_user("user-123")

                # 验证返回类型
                assert isinstance(result, ORJSONResponse)

                # 验证调用了正确的服务
                mock_get_user.assert_called_once_with("user-123")
                mock_get_roles.assert_called_once_with("user-123")
                mock_get_perms.assert_called_once_with("user-123")

                # 验证返回内容（需要从 ORJSONResponse 中提取）
                content = result.body.decode('utf-8')
                data = json.loads(content)

                assert data["code"] == 200
                assert data["msg"] == "success"

                user_data = data["data"]
                assert user_data["id"] == "user-123"
                assert user_data["username"] == "testuser"
                assert set(user_data["roles"]) == {"admin", "viewer"}
                assert set(user_data["permissions"]) == {"iam:user:read", "iam:role:read"}


@pytest.mark.asyncio
async def test_get_current_user_not_found():
    """用户不存在时应抛出 404 错误"""

    with patch("iam.controllers.user_controller.user_service.get_by_id", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("non-existent-user")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "用户不存在"
        mock_get_user.assert_called_once_with("non-existent-user")


@pytest.mark.asyncio
async def test_get_current_user_empty_roles_and_permissions():
    """用户无角色和权限时应返回空列表"""

    # Mock user
    mock_user = MagicMock()
    mock_user.id = "user-456"
    mock_user.tenant_id = "tenant-123"
    mock_user.username = "basicuser"
    mock_user.email = "basic@example.com"
    mock_user.phone = None
    mock_user.nickname = "Basic"
    mock_user.avatar = None
    mock_user.status = "active"
    mock_user.profile_completed = True
    mock_user.is_email_verified = False
    mock_user.is_phone_verified = False
    mock_user.last_login_at = None
    mock_user.created_at = "2024-01-01T00:00:00Z"

    with patch("iam.controllers.user_controller.user_service.get_by_id", new_callable=AsyncMock) as mock_get_user:
        with patch("iam.controllers.user_controller.user_roles_service.get_user_roles", new_callable=AsyncMock) as mock_get_roles:
            with patch("iam.controllers.user_controller.permission_check_service.get_user_permissions", new_callable=AsyncMock) as mock_get_perms:
                mock_get_user.return_value = mock_user
                mock_get_roles.return_value = []  # 无角色
                mock_get_perms.return_value = []  # 无权限

                result = await get_current_user("user-456")

                # 验证返回类型
                assert isinstance(result, ORJSONResponse)

                # 验证返回内容
                content = result.body.decode('utf-8')
                data = json.loads(content)

                assert data["code"] == 200
                assert data["msg"] == "success"

                user_data = data["data"]
                assert user_data["id"] == "user-456"
                assert user_data["username"] == "basicuser"
                assert user_data["roles"] == []
                assert user_data["permissions"] == []
