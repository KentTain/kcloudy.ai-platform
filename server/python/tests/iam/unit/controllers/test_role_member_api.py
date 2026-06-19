"""角色成员管理 API 端点测试

测试角色成员管理相关的 API 端点：
- GET /roles/{role_id}/members
- POST /roles/{role_id}/members
- DELETE /roles/{role_id}/members/{user_id}
- GET /roles/options
- GET /roles/{role_id}/menus
- POST /roles/{role_id}/menus
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from iam.controllers.admin.role_controller import (
    add_role_members,
    assign_role_menus,
    get_role_members,
    get_role_menus,
    remove_role_member,
)


class TestGetRoleMembers:
    """测试 GET /roles/{role_id}/members 端点"""

    @pytest.mark.asyncio
    async def test_get_role_members_success(self, session: AsyncSession):
        """成功获取角色成员列表"""
        mock_members = [
            {
                "user_id": "user-1",
                "username": "user1",
                "nickname": "用户1",
                "email": "user1@example.com",
                "phone": "13800138001",
                "status": "active",
            },
            {
                "user_id": "user-2",
                "username": "user2",
                "nickname": "用户2",
                "email": "user2@example.com",
                "phone": "13800138002",
                "status": "inactive",
            },
        ]

        with patch(
            "iam.controllers.admin.role_controller.role_member_service.get_role_members",
            new_callable=AsyncMock,
            return_value=mock_members,
        ):
            result = await get_role_members("role-123", session)

            # 验证返回类型
            assert isinstance(result, ORJSONResponse)

            # 验证返回内容
            content = bytes(result.body).decode("utf-8")
            data = json.loads(content)

            assert data["code"] == 200
            assert data["msg"] == "OK"
            assert len(data["data"]) == 2
            assert data["data"][0]["user_id"] == "user-1"
            assert data["data"][1]["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_get_role_members_empty(self, session: AsyncSession):
        """角色无成员时返回空列表"""
        with patch(
            "iam.controllers.admin.role_controller.role_member_service.get_role_members",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await get_role_members("role-empty", session)

            content = bytes(result.body).decode("utf-8")
            data = json.loads(content)

            assert data["code"] == 200
            assert data["data"] == []


class TestAddRoleMembers:
    """测试 POST /roles/{role_id}/members 端点"""

    @pytest.mark.asyncio
    async def test_add_role_members_success(self, session: AsyncSession):
        """成功添加角色成员"""
        from iam.schemas.role import RoleMemberAssignRequest

        with patch(
            "iam.controllers.admin.role_controller.role_member_service.add_role_members",
            new_callable=AsyncMock,
            return_value=3,
        ):
            data = RoleMemberAssignRequest(user_ids=["user-1", "user-2", "user-3"])
            result = await add_role_members("role-123", data, session)

            # 验证返回类型
            assert isinstance(result, ORJSONResponse)

            # 验证返回内容
            content = bytes(result.body).decode("utf-8")
            response_data = json.loads(content)

            assert response_data["code"] == 200
            assert response_data["msg"] == "OK"
            assert response_data["data"]["added"] == 3

    @pytest.mark.asyncio
    async def test_add_role_members_role_not_found(self, session: AsyncSession):
        """角色不存在时抛出 400 错误"""
        from iam.schemas.role import RoleMemberAssignRequest

        with patch(
            "iam.controllers.admin.role_controller.role_member_service.add_role_members",
            new_callable=AsyncMock,
            side_effect=ValueError("角色不存在"),
        ):
            data = RoleMemberAssignRequest(user_ids=["user-1"])

            with pytest.raises(HTTPException) as exc_info:
                await add_role_members("nonexistent-role", data, session)

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "角色不存在"


class TestRemoveRoleMember:
    """测试 DELETE /roles/{role_id}/members/{user_id} 端点"""

    @pytest.mark.asyncio
    async def test_remove_role_member_success(self, session: AsyncSession):
        """成功移除角色成员"""
        with patch(
            "iam.controllers.admin.role_controller.role_member_service.remove_role_member",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await remove_role_member("role-123", "user-1", session)

            # 验证返回类型
            assert isinstance(result, ORJSONResponse)

            # 验证返回内容
            content = bytes(result.body).decode("utf-8")
            data = json.loads(content)

            assert data["code"] == 200
            assert data["msg"] == "OK"

    @pytest.mark.asyncio
    async def test_remove_role_member_not_found(self, session: AsyncSession):
        """用户不是角色成员时抛出 404 错误"""
        with patch(
            "iam.controllers.admin.role_controller.role_member_service.remove_role_member",
            new_callable=AsyncMock,
            return_value=False,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await remove_role_member("role-123", "nonexistent-user", session)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "该用户不是此角色成员"


class TestRoleMenuManagement:
    """测试角色菜单管理端点"""

    @pytest.mark.asyncio
    async def test_get_role_menus_success(self, session: AsyncSession):
        """成功获取角色菜单列表"""
        with patch(
            "iam.controllers.admin.role_controller.role_member_service.get_role_menus",
            new_callable=AsyncMock,
            return_value=["menu-1", "menu-2", "menu-3"],
        ):
            result = await get_role_menus("role-123", session)

            # 验证返回类型
            assert isinstance(result, ORJSONResponse)

            # 验证返回内容
            content = bytes(result.body).decode("utf-8")
            data = json.loads(content)

            assert data["code"] == 200
            assert data["msg"] == "OK"
            assert data["data"] == ["menu-1", "menu-2", "menu-3"]

    @pytest.mark.asyncio
    async def test_assign_role_menus_success(self, session: AsyncSession):
        """成功分配角色菜单"""
        from iam.schemas.role import RoleMenuAssignRequest

        with patch(
            "iam.controllers.admin.role_controller.role_member_service.assign_role_menus",
            new_callable=AsyncMock,
        ):
            data = RoleMenuAssignRequest(menu_ids=["menu-1", "menu-2"])
            result = await assign_role_menus("role-123", data, session)

            # 验证返回类型
            assert isinstance(result, ORJSONResponse)

            # 验证返回内容
            content = bytes(result.body).decode("utf-8")
            response_data = json.loads(content)

            assert response_data["code"] == 200
            assert response_data["msg"] == "OK"
