"""
IAM 角色控制器单元测试

测试控制器的错误处理逻辑。
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


def _make_mock_role(**kwargs):
    """创建 mock 角色对象"""
    defaults = {
        "id": "role-1",
        "code": "admin",
        "name": "管理员",
        "tenant_id": "tenant-1",
        "description": "管理员角色",
        "created_at": datetime(2026, 1, 1),
        "updated_at": datetime(2026, 1, 1),
        "is_system": False,
    }
    defaults.update(**kwargs)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


@pytest.mark.asyncio
class TestCreateRole:
    """create_role 控制器测试"""

    async def test_create_role_with_duplicate_code_raises_error(self, mock_session):
        """角色编码重复时抛出错误"""
        from iam.controllers.admin.role_controller import create_role
        from iam.schemas.role import RoleCreate

        with patch("iam.controllers.admin.role_controller.role_service.create") as mock_create:
            mock_create.side_effect = ValueError("角色编码已存在")

            data = RoleCreate(code="admin", name="管理员", description=None)

            with pytest.raises(HTTPException) as exc_info:
                await create_role(data=data, session=mock_session)

            assert exc_info.value.status_code == 400
            assert "角色编码已存在" in exc_info.value.detail


@pytest.mark.asyncio
class TestGetRole:
    """get_role 控制器测试"""

    async def test_get_role_not_found_raises_404(self, mock_session):
        """角色不存在时抛出 404"""
        from iam.controllers.admin.role_controller import get_role

        with patch("iam.controllers.admin.role_controller.role_service.get_by_id") as mock_get:
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_role(role_id="nonexistent", session=mock_session)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "角色不存在"


@pytest.mark.asyncio
class TestUpdateRole:
    """update_role 控制器测试"""

    async def test_update_role_with_invalid_data_raises_error(self, mock_session):
        """更新数据无效时抛出错误"""
        from iam.controllers.admin.role_controller import update_role
        from iam.schemas.role import RoleUpdate

        with patch("iam.controllers.admin.role_controller.role_service.update") as mock_update:
            mock_update.side_effect = ValueError("更新失败")

            data = RoleUpdate(name="", description=None)

            with pytest.raises(HTTPException) as exc_info:
                await update_role(role_id="role-1", data=data, session=mock_session)

            assert exc_info.value.status_code == 400


@pytest.mark.asyncio
class TestDeleteRole:
    """delete_role 控制器测试"""

    async def test_delete_role_with_error_raises_400(self, mock_session):
        """删除失败时抛出错误"""
        from iam.controllers.admin.role_controller import delete_role

        with patch("iam.controllers.admin.role_controller.role_service.delete") as mock_delete:
            mock_delete.side_effect = ValueError("角色正在使用中")

            with pytest.raises(HTTPException) as exc_info:
                await delete_role(role_id="role-1", session=mock_session)

            assert exc_info.value.status_code == 400
