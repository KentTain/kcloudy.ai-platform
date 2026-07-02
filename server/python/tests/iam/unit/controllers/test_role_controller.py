"""
IAM 角色控制器单元测试

测试控制器的参数校验和错误处理逻辑。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from iam.controllers.admin.role_controller import (
    create_role,
    delete_role,
    get_role,
    get_role_options,
    list_roles,
    update_role,
)
from iam.models import Role


def _make_mock_role(**kwargs):
    """创建 mock 角色对象，包含所有必要属性"""
    defaults = {
        "id": "role-1",
        "code": "admin",
        "name": "管理员",
        "tenant_id": "tenant-1",
        "description": "管理员角色",
        "created_at": None,
        "updated_at": None,
    }
    defaults.update(**kwargs)

    # 使用简单对象而不是 MagicMock(spec=Role)，避免 pydantic 验证问题
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


@pytest.mark.asyncio
class TestListRoles:

    async def test_list_roles_returns_paginated_result(self, mock_session):
        """返回分页的角色列表"""
        mock_roles = [_make_mock_role(id="role-1"), _make_mock_role(id="role-2")]

        with patch("iam.controllers.admin.role_controller.role_service.list_roles") as mock_list:
            mock_list.return_value = (mock_roles, 2)

            from iam.schemas.role import RolePaginatedQuery
            query = RolePaginatedQuery(page=1, page_size=10)
            result = await list_roles(query=query, tenant_id=None, session=mock_session)

        assert result["code"] == 200
        assert result["total"] == 2
        assert len(result["data"]) == 2
        mock_list.assert_called_once()


@pytest.mark.asyncio
class TestCreateRole:

    async def test_create_role_with_duplicate_code_raises_error(self, mock_session):
        """角色编码重复时抛出错误"""
        with patch("iam.controllers.admin.role_controller.role_service.create") as mock_create:
            mock_create.side_effect = ValueError("角色编码已存在")

            from iam.schemas.role import RoleCreate
            data = RoleCreate(code="admin", name="管理员", description=None)

            with pytest.raises(HTTPException) as exc_info:
                await create_role(data=data, session=mock_session)

            assert exc_info.value.status_code == 400
            assert "角色编码已存在" in exc_info.value.detail


@pytest.mark.asyncio
class TestGetRole:

    async def test_get_role_not_found_raises_404(self, mock_session):
        """角色不存在时抛出 404"""
        with patch("iam.controllers.admin.role_controller.role_service.get_by_id") as mock_get:
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_role(role_id="nonexistent", session=mock_session)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "角色不存在"


@pytest.mark.asyncio
class TestUpdateRole:

    async def test_update_role_with_invalid_data_raises_error(self, mock_session):
        """更新数据无效时抛出错误"""
        with patch("iam.controllers.admin.role_controller.role_service.update") as mock_update:
            mock_update.side_effect = ValueError("更新失败")

            from iam.schemas.role import RoleUpdate
            data = RoleUpdate(name="", description=None)

            with pytest.raises(HTTPException) as exc_info:
                await update_role(role_id="role-1", data=data, session=mock_session)

            assert exc_info.value.status_code == 400


@pytest.mark.asyncio
class TestDeleteRole:

    async def test_delete_role_success(self, mock_session):
        """成功删除角色"""
        with patch("iam.controllers.admin.role_controller.role_service.delete") as mock_delete:
            mock_delete.return_value = True

            result = await delete_role(role_id="role-1", session=mock_session)

        assert result["code"] == 200
        mock_delete.assert_called_once_with(mock_session, "role-1")

    async def test_delete_role_with_error_raises_400(self, mock_session):
        """删除失败时抛出错误"""
        with patch("iam.controllers.admin.role_controller.role_service.delete") as mock_delete:
            mock_delete.side_effect = ValueError("角色正在使用中")

            with pytest.raises(HTTPException) as exc_info:
                await delete_role(role_id="role-1", session=mock_session)

            assert exc_info.value.status_code == 400


@pytest.mark.asyncio
class TestGetRoleOptions:

    async def test_get_role_options_returns_list(self, mock_session):
        """返回角色选项列表"""
        mock_role = _make_mock_role()

        with patch("iam.controllers.admin.role_controller.user_role_service.get_role_options") as mock_get:
            mock_get.return_value = [mock_role]

            result = await get_role_options(session=mock_session)

        assert result["code"] == 200
        assert len(result["data"]) == 1
        mock_get.assert_called_once_with(mock_session)
