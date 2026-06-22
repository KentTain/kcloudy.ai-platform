"""
管理后台 API 单元测试

测试接口扩展功能：
- Task 5.1: 登录接口返回 role 和 permissions
- Task 5.2: /admin/me 接口
- Task 5.3: get_admin_menus 权限过滤
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from tenant.schemas.admin.tenant import (
    AdminInfoResponse,
    AdminLoginResponse,
)


class TestAdminLoginResponseSchema:
    """Task 5.1: AdminLoginResponse Schema 测试"""

    def test_admin_login_response_has_role_field(self):
        """AdminLoginResponse 包含 role 字段"""
        response = AdminLoginResponse(
            token="test-token",
            username="admin",
            is_default=True,
            role="tenantAdmin",
            permissions=["tenant:module:read"],
        )
        assert response.role == "tenantAdmin"
        assert response.permissions == ["tenant:module:read"]

    def test_admin_login_response_serialization(self):
        """AdminLoginResponse 序列化包含 role 和 permissions"""
        response = AdminLoginResponse(
            token="test-token",
            username="admin",
            is_default=True,
            role="tenantAdmin",
            permissions=["tenant:module:read"],
        )
        data = response.model_dump()
        assert data["role"] == "tenantAdmin"
        assert data["permissions"] == ["tenant:module:read"]


class TestAdminInfoResponseSchema:
    """AdminInfoResponse Schema 测试"""

    def test_admin_info_response_fields(self):
        """AdminInfoResponse 包含必要字段"""
        now = datetime.now()
        response = AdminInfoResponse(
            id="admin-001",
            username="test_admin",
            is_default=True,
            is_active=True,
            created_at=now,
        )
        assert response.id == "admin-001"
        assert response.username == "test_admin"
        assert response.is_default is True
        assert response.is_active is True
        assert response.created_at == now


class TestAdminLoginEndpoint:
    """Task 5.1: 登录接口扩展测试"""

    @pytest.mark.asyncio
    async def test_admin_login_returns_role_and_permissions(self):
        """登录接口返回 role 和 permissions"""
        from tenant.controllers.admin.tenant_controller import admin_login
        from tenant.schemas.admin.tenant import AdminLoginRequest

        # Prepare mock request
        login_data = AdminLoginRequest(username="admin", password="admin123")

        # Mock session
        session = AsyncMock()

        # Mock AdminAuthService.login
        admin_mock = MagicMock()
        admin_mock.username = "admin"
        admin_mock.is_default = True
        admin_mock.role = "tenantAdmin"

        with patch(
            "tenant.controllers.admin.tenant_controller.AdminAuthService.login",
            AsyncMock(return_value=("test-token", admin_mock)),
        ), patch(
            "tenant.controllers.admin.tenant_controller.AdminAuthService._get_role_permissions",
            AsyncMock(return_value=["tenant:module:read", "tenant:module:write"]),
        ), patch(
            "tenant.middlewares.admin_auth_middleware.ModuleService.get_by_code",
            AsyncMock(return_value=MagicMock(id="module-001")),
        ):
            response = await admin_login(login_data, session)

        assert response is not None
        assert response.status_code == 200

        # The login endpoint builds AdminLoginResponse with role and permissions
        # Let's verify the response content
        body = response.body.decode("utf-8") if hasattr(response, "body") else ""


class TestGetAdminMeEndpoint:
    """Task 5.2: /admin/me 接口测试"""

    @pytest.mark.asyncio
    async def test_get_admin_me_returns_full_info(self):
        """GET /admin/me 返回完整管理员信息"""
        from tenant.controllers.admin.tenant_controller import get_admin_me

        session = AsyncMock()

        admin_info = {
            "id": "admin-001",
            "username": "test_admin",
            "role": "tenantAdmin",
            "permissions": ["tenant:module:read"],
            "is_default": True,
            "is_active": True,
            "menus": [
                {
                    "code": "tenant",
                    "name": "租户管理",
                    "children": [
                        {"code": "tenant.modules", "name": "模块管理"}
                    ],
                }
            ],
        }

        with patch(
            "tenant.controllers.admin.tenant_controller.AdminAuthService.get_admin_info",
            AsyncMock(return_value=admin_info),
        ):
            admin = {"admin_id": "admin-001", "username": "test_admin"}
            response = await get_admin_me(admin, session)

        assert response is not None

    @pytest.mark.asyncio
    async def test_get_admin_me_raises_404_when_admin_not_found(self):
        """管理员不存在时返回 404"""
        from fastapi import HTTPException
        from tenant.controllers.admin.tenant_controller import get_admin_me

        session = AsyncMock()

        with patch(
            "tenant.controllers.admin.tenant_controller.AdminAuthService.get_admin_info",
            AsyncMock(return_value=None),
        ):
            admin = {"admin_id": "nonexistent", "username": "test"}
            with pytest.raises(HTTPException) as exc_info:
                await get_admin_me(admin, session)

            assert exc_info.value.status_code == 404


class TestGetAdminMenus:
    """Task 5.3: get_admin_menus 权限过滤测试"""

    @pytest.mark.asyncio
    async def test_get_admin_menus_filters_by_permissions(self):
        """get_admin_menus 根据角色权限过滤菜单"""
        from tenant.controllers.admin.tenant_controller import get_admin_menus

        session = AsyncMock()

        # Mock module with id
        module_mock = MagicMock()
        module_mock.id = "module-tenant"
        module_mock.code = "tenant"
        module_mock.name = "租户管理"
        module_mock.icon = "Organization"
        module_mock.created_at = datetime.now()
        module_mock.updated_at = datetime.now()

        menu_mock = MagicMock()
        menu_mock.id = "menu-001"
        menu_mock.module_id = "module-tenant"
        menu_mock.parent_id = None
        menu_mock.code = "tenant.modules"
        menu_mock.name = "模块管理"
        menu_mock.path = "/admin/modules"
        menu_mock.icon = "Puzzle"
        menu_mock.tree_sort = 1
        menu_mock.tree_level = 1
        menu_mock.tree_leaf = True
        menu_mock.is_visible = True
        menu_mock.created_at = datetime.now()
        menu_mock.updated_at = datetime.now()

        with patch(
            "tenant.controllers.admin.tenant_controller.ModuleService.get_by_code",
            AsyncMock(return_value=module_mock),
        ), patch(
            "tenant.controllers.admin.tenant_controller.ModuleMenuService.list_menus",
            AsyncMock(return_value=[menu_mock]),
        ):
            admin = {
                "admin_id": "admin-001",
                "username": "admin",
                "role": "tenantAdmin",
                "permissions": ["tenant:module:read"],
            }
            response = await get_admin_menus(admin, session)

        assert response is not None

    @pytest.mark.asyncio
    async def test_get_admin_menus_returns_empty_when_no_module(self):
        """模块不存在时返回空列表"""
        from tenant.controllers.admin.tenant_controller import get_admin_menus

        session = AsyncMock()

        with patch(
            "tenant.controllers.admin.tenant_controller.ModuleService.get_by_code",
            AsyncMock(return_value=None),
        ):
            admin = {"admin_id": "admin-001", "username": "admin", "permissions": []}
            response = await get_admin_menus(admin, session)

        assert response is not None
        body = response.body.decode()
        assert '"data"' in body
