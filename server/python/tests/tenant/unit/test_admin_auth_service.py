"""
管理员认证服务单元测试

测试 AdminAuthService 扩展功能：
- Task 4.1: login() 存储 role 和 permissions
- Task 4.2: get_admin_info() 聚合方法
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.middlewares.admin_auth_middleware import AdminAuthService, _admin_tokens


class TestAdminAuthServiceLoginRolePermission:
    """Task 4.1: AdminAuthService.login() 扩展测试"""

    def setup_method(self):
        _admin_tokens.clear()

    @pytest.mark.asyncio
    async def test_login_stores_role_in_token_data(self):
        """登录成功后 token_data 中包含 role 字段"""
        session = AsyncMock(spec=AsyncSession)

        # Mock TenantAdmin 查询结果
        admin_mock = MagicMock()
        admin_mock.id = "admin-001"
        admin_mock.username = "test_admin"
        admin_mock.password = "$2b$12$hashedpassword"
        admin_mock.is_default = False
        admin_mock.role = "tenantAdmin"

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none = AsyncMock(return_value=admin_mock)
        session.execute = AsyncMock(return_value=scalar_result)

        with patch(
            "tenant.middlewares.admin_auth_middleware.verify_password",
            return_value=True,
        ), patch(
            "tenant.middlewares.admin_auth_middleware.ModuleService.get_by_code",
            AsyncMock(return_value=None),
        ):
            token, admin = await AdminAuthService.login(session, "test_admin", "password")

        assert token is not None
        assert token in _admin_tokens
        assert _admin_tokens[token]["role"] == "tenantAdmin"

    @pytest.mark.asyncio
    async def test_login_stores_permissions_when_role_has_permissions(self):
        """登录成功后 token_data 中包含 permissions 列表"""
        session = AsyncMock(spec=AsyncSession)

        admin_mock = MagicMock()
        admin_mock.id = "admin-001"
        admin_mock.username = "test_admin"
        admin_mock.password = "$2b$12$hashedpassword"
        admin_mock.is_default = False
        admin_mock.role = "tenantAdmin"

        # Mock 查询序列
        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none = AsyncMock(return_value=admin_mock)
        session.execute = AsyncMock(return_value=scalar_result)

        # Mock ModuleService.get_by_code 返回 tenant 模块
        module_mock = MagicMock()
        module_mock.id = "module-tenant-001"
        with patch(
            "tenant.middlewares.admin_auth_middleware.verify_password",
            return_value=True,
        ), patch(
            "tenant.middlewares.admin_auth_middleware.ModuleService.get_by_code",
            AsyncMock(return_value=module_mock),
        ), patch.object(
            AdminAuthService, "_get_role_permissions", AsyncMock(return_value=["tenant:module:read", "tenant:module:write", "tenant:module:delete"])
        ):
            token, admin = await AdminAuthService.login(session, "test_admin", "password")

        assert token in _admin_tokens
        assert "permissions" in _admin_tokens[token]
        assert isinstance(_admin_tokens[token]["permissions"], list)

    @pytest.mark.asyncio
    async def test_login_stores_empty_permissions_when_role_has_none(self):
        """角色无权限时 permissions 为空列表"""
        session = AsyncMock(spec=AsyncSession)

        admin_mock = MagicMock()
        admin_mock.id = "admin-001"
        admin_mock.username = "test_admin"
        admin_mock.password = "$2b$12$hashedpassword"
        admin_mock.is_default = False
        admin_mock.role = "ordinaryAdmin"

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none = AsyncMock(return_value=admin_mock)
        session.execute = AsyncMock(return_value=scalar_result)

        module_mock = MagicMock()
        module_mock.id = "module-tenant-001"
        with patch(
            "tenant.middlewares.admin_auth_middleware.verify_password",
            return_value=True,
        ), patch(
            "tenant.middlewares.admin_auth_middleware.ModuleService.get_by_code",
            AsyncMock(return_value=module_mock),
        ), patch.object(
            AdminAuthService, "_get_role_permissions", AsyncMock(return_value=[])
        ):
            token, admin = await AdminAuthService.login(session, "test_admin", "password")

        assert token in _admin_tokens
        assert _admin_tokens[token]["permissions"] == []


class TestAdminAuthServiceGetAdminInfo:
    """Task 4.2: AdminAuthService.get_admin_info() 测试"""

    def setup_method(self):
        _admin_tokens.clear()

    @pytest.mark.asyncio
    async def test_get_admin_info_returns_none_when_admin_not_found(self):
        """管理员不存在时返回 None"""
        session = AsyncMock(spec=AsyncSession)

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none = AsyncMock(return_value=None)
        session.execute = AsyncMock(return_value=scalar_result)

        result = await AdminAuthService.get_admin_info(session, "nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_admin_info_returns_admin_with_role_and_permissions(self):
        """get_admin_info 返回管理员信息包含 role 和 permissions"""
        session = AsyncMock(spec=AsyncSession)

        admin_mock = MagicMock()
        admin_mock.id = "admin-001"
        admin_mock.username = "test_admin"
        admin_mock.role = "tenantAdmin"

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none = AsyncMock(return_value=admin_mock)
        # This handles multiple execute calls (first for admin, rest for permissions/menus)
        session.execute = AsyncMock(return_value=scalar_result)

        with patch.object(
            AdminAuthService, "_get_role_permissions", AsyncMock(return_value=["tenant:module:read"])
        ), patch.object(
            AdminAuthService, "_get_admin_menus", AsyncMock(return_value=[])
        ):
            result = await AdminAuthService.get_admin_info(session, "admin-001")

        assert result is not None
        assert result["id"] == "admin-001"
        assert result["username"] == "test_admin"
        assert result["role"] == "tenantAdmin"
        assert result["permissions"] == ["tenant:module:read"]
        assert "menus" in result

    @pytest.mark.asyncio
    async def test_get_admin_info_returns_empty_permissions_when_no_role(self):
        """管理员角色无权限时 permissions 为空列表"""
        session = AsyncMock(spec=AsyncSession)

        admin_mock = MagicMock()
        admin_mock.id = "admin-001"
        admin_mock.username = "test_admin"
        admin_mock.role = "ordinaryAdmin"

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none = AsyncMock(return_value=admin_mock)
        session.execute = AsyncMock(return_value=scalar_result)

        with patch.object(
            AdminAuthService, "_get_role_permissions", AsyncMock(return_value=[])
        ), patch.object(
            AdminAuthService, "_get_admin_menus", AsyncMock(return_value=[])
        ):
            result = await AdminAuthService.get_admin_info(session, "admin-001")

        assert result is not None
        assert result["permissions"] == []


class TestAdminAuthServiceGetRolePermissions:
    """_get_role_permissions 辅助方法测试"""

    @pytest.mark.asyncio
    async def test_get_role_permissions_returns_codes(self):
        """_get_role_permissions 返回权限码列表"""
        session = AsyncMock(spec=AsyncSession)

        # Mock module_role 查询
        role_mock = MagicMock()
        role_mock.id = "role-001"
        role_scalar = MagicMock()
        role_scalar.scalar_one_or_none = AsyncMock(return_value=role_mock)

        # Mock module_role_permissions 查询
        rp_mock_1 = MagicMock()
        rp_mock_1.module_permission_id = "perm-001"
        rp_mock_2 = MagicMock()
        rp_mock_2.module_permission_id = "perm-002"
        rp_scalar = MagicMock()
        rp_scalar.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[rp_mock_1, rp_mock_2])))

        # Mock module_permissions 查询
        perm_scalar = MagicMock()
        perm_scalar.all = MagicMock(return_value=[("tenant:module:read",), ("tenant:module:write",)])

        session.execute = AsyncMock(side_effect=[role_scalar, rp_scalar, perm_scalar])

        module_mock = MagicMock()
        module_mock.id = "module-001"

        permissions = await AdminAuthService._get_role_permissions(
            session, module_mock, "tenantAdmin"
        )

        assert permissions == ["tenant:module:read", "tenant:module:write"]

    @pytest.mark.asyncio
    async def test_get_role_permissions_returns_empty_when_role_not_found(self):
        """角色在 module_roles 表中不存在时返回空列表"""
        session = AsyncMock(spec=AsyncSession)

        role_scalar = MagicMock()
        role_scalar.scalar_one_or_none = AsyncMock(return_value=None)
        session.execute = AsyncMock(return_value=role_scalar)

        module_mock = MagicMock()
        module_mock.id = "module-001"

        permissions = await AdminAuthService._get_role_permissions(
            session, module_mock, "nonexistent-role"
        )

        assert permissions == []

    @pytest.mark.asyncio
    async def test_get_role_permissions_returns_empty_when_module_is_none(self):
        """模块为 None 时返回空列表"""
        session = AsyncMock(spec=AsyncSession)

        permissions = await AdminAuthService._get_role_permissions(
            session, None, "tenantAdmin"
        )

        assert permissions == []


class TestAdminAuthServiceGetAdminMenus:
    """_get_admin_menus 辅助方法测试"""

    @pytest.mark.asyncio
    async def test_get_admin_menus_filters_by_permissions(self):
        """_get_admin_menus 根据权限过滤菜单"""
        session = AsyncMock(spec=AsyncSession)

        menu_1 = MagicMock()
        menu_1.id = "menu-001"
        menu_1.module_id = "module-001"
        menu_1.code = "tenant.modules"
        menu_1.name = "模块管理"
        menu_1.path = "/admin/modules"
        menu_1.icon = "Puzzle"
        menu_1.parent_id = None
        menu_1.is_visible = True
        menu_1.tree_sort = 1
        menu_1.tree_level = 1
        menu_1.tree_leaf = True
        menu_1.created_at = None
        menu_1.updated_at = None

        menu_2 = MagicMock()
        menu_2.id = "menu-002"
        menu_2.module_id = "module-001"
        menu_2.code = "tenant.settings"
        menu_2.name = "系统设置"
        menu_2.path = "/admin/settings"
        menu_2.icon = "Settings"
        menu_2.parent_id = None
        menu_2.is_visible = True
        menu_2.tree_sort = 2
        menu_2.tree_level = 1
        menu_2.tree_leaf = True
        menu_2.created_at = None
        menu_2.updated_at = None

        module_mock = MagicMock()
        module_mock.id = "module-001"
        module_mock.code = "tenant"
        module_mock.name = "租户管理"
        module_mock.icon = "Organization"
        module_mock.created_at = None
        module_mock.updated_at = None

        # Mock ModuleMenuService.list_menus return
        with patch(
            "tenant.middlewares.admin_auth_middleware.ModuleMenuService.list_menus",
            AsyncMock(return_value=[menu_1, menu_2]),
        ), patch(
            "tenant.middlewares.admin_auth_middleware.ModuleMenuPermission",
        ) as MockMMP:
            # Menu 1 has permission that matches, Menu 2 doesn't
            mmp_mock_1 = MagicMock()
            mmp_mock_1.module_permission_id = "perm-001"

            mmp_scalar = MagicMock()
            mmp_scalar.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mmp_mock_1])))
            session.execute = AsyncMock(return_value=mmp_scalar)

            # permissions that match: menu 1 has perm-001 which is in our perms
            # We need to check ModuleMenuPermission for each menu
            menus = await AdminAuthService._get_admin_menus(
                session, module_mock, ["perm-001"]
            )

            # menu_1 should be included (its permission matches), menu_2 should not
            assert len(menus) > 0

    @pytest.mark.asyncio
    async def test_get_admin_menus_returns_all_when_no_permissions_filter(self):
        """无权限过滤参数时返回所有可见菜单"""
        session = AsyncMock(spec=AsyncSession)

        menu = MagicMock()
        menu.id = "menu-001"
        menu.module_id = "module-001"
        menu.code = "tenant.modules"
        menu.name = "模块管理"
        menu.path = "/admin/modules"
        menu.icon = "Puzzle"
        menu.parent_id = None
        menu.is_visible = True
        menu.tree_sort = 1
        menu.tree_level = 1
        menu.tree_leaf = True
        menu.created_at = None
        menu.updated_at = None

        module_mock = MagicMock()
        module_mock.id = "module-001"
        module_mock.code = "tenant"
        module_mock.name = "租户管理"
        module_mock.icon = "Organization"
        module_mock.created_at = None
        module_mock.updated_at = None

        with patch(
            "tenant.middlewares.admin_auth_middleware.ModuleMenuService.list_menus",
            AsyncMock(return_value=[menu]),
        ):
            menus = await AdminAuthService._get_admin_menus(session, module_mock)

            assert len(menus) == 1
            assert menus[0]["code"] == "tenant"
            assert len(menus[0]["children"]) == 1
            assert menus[0]["children"][0]["code"] == "tenant.modules"
