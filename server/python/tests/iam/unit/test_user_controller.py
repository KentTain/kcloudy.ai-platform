"""用户控制器测试 - /me 接口返回角色权限"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import ORJSONResponse

from iam.controllers.console.user_controller import get_current_user
from iam.schemas.user import UserDetailResponse


@pytest.mark.asyncio
async def test_get_current_user_returns_roles_and_permissions(session):
    """get_current_user 应返回用户的角色和权限"""

    # Mock UserDetailResponse
    mock_user_detail = MagicMock(spec=UserDetailResponse)
    mock_user_detail.id = "user-123"
    mock_user_detail.username = "testuser"
    mock_user_detail.roles = ["admin", "viewer"]
    mock_user_detail.permissions = ["iam:user:read", "iam:role:read"]
    mock_user_detail.model_dump.return_value = {
        "id": "user-123",
        "username": "testuser",
        "roles": ["admin", "viewer"],
        "permissions": ["iam:user:read", "iam:role:read"],
    }

    with patch("iam.controllers.console.user_controller.user_service.get_user_detail", new_callable=AsyncMock) as mock_get_detail:
        mock_get_detail.return_value = mock_user_detail

        result = await get_current_user("user-123", session)

        # 验证返回类型
        assert isinstance(result, ORJSONResponse)

        # 验证调用了正确的服务（带 session 参数）
        mock_get_detail.assert_called_once_with(session, "user-123")

        # 验证返回内容
        content = bytes(result.body).decode('utf-8')
        data = json.loads(content)

        assert data["code"] == 200
        assert data["msg"] == "OK"  # Success 默认 msg 是 "OK"

        user_data = data["data"]
        assert user_data["id"] == "user-123"
        assert user_data["username"] == "testuser"
        assert set(user_data["roles"]) == {"admin", "viewer"}
        assert set(user_data["permissions"]) == {"iam:user:read", "iam:role:read"}


@pytest.mark.asyncio
async def test_get_current_user_not_found(session):
    """用户不存在时应抛出 404 错误"""

    with patch("iam.controllers.console.user_controller.user_service.get_user_detail", new_callable=AsyncMock) as mock_get_detail:
        mock_get_detail.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("non-existent-user", session)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "用户不存在"
        mock_get_detail.assert_called_once_with(session, "non-existent-user")


@pytest.mark.asyncio
async def test_get_current_user_empty_roles_and_permissions(session):
    """用户无角色和权限时应返回空列表"""

    # Mock UserDetailResponse
    mock_user_detail = MagicMock(spec=UserDetailResponse)
    mock_user_detail.id = "user-456"
    mock_user_detail.username = "basicuser"
    mock_user_detail.roles = []
    mock_user_detail.permissions = []
    mock_user_detail.model_dump.return_value = {
        "id": "user-456",
        "username": "basicuser",
        "roles": [],
        "permissions": [],
    }

    with patch("iam.controllers.console.user_controller.user_service.get_user_detail", new_callable=AsyncMock) as mock_get_detail:
        mock_get_detail.return_value = mock_user_detail

        result = await get_current_user("user-456", session)

        # 验证返回类型
        assert isinstance(result, ORJSONResponse)

        # 验证返回内容
        content = bytes(result.body).decode('utf-8')
        data = json.loads(content)

        assert data["code"] == 200
        assert data["msg"] == "OK"  # Success 默认 msg 是 "OK"

        user_data = data["data"]
        assert user_data["id"] == "user-456"
        assert user_data["username"] == "basicuser"
        assert user_data["roles"] == []
        assert user_data["permissions"] == []
