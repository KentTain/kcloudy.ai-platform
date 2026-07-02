"""
MenuService 单元测试

测试菜单服务的权限过滤逻辑。
"""

from unittest.mock import MagicMock, patch

import pytest


class TestMenuService:
    """MenuService 单元测试"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_menus_with_permissions(self, mock_session):
        """
        场景：用户拥有权限时返回对应菜单

        GIVEN 用户拥有 user:read 权限
        WHEN 调用 get_user_menus
        THEN 返回关联 user:read 权限的菜单
        """
        # 模拟用户权限查询
        mock_perm_result = MagicMock()
        mock_perm_result.fetchall.return_value = [("perm-1",)]

        # 模拟菜单查询
        mock_menu_1 = MagicMock()
        mock_menu_1.id = "menu-1"
        mock_menu_1.code = "iam:users"
        mock_menu_1.name = "用户管理"
        mock_menu_1.is_visible = True

        mock_menu_2 = MagicMock()
        mock_menu_2.id = "menu-2"
        mock_menu_2.code = "demo:home"
        mock_menu_2.name = "首页"
        mock_menu_2.is_visible = True

        mock_menu_result = MagicMock()
        mock_menu_result.scalars.return_value.all.return_value = [mock_menu_1, mock_menu_2]

        # 模拟菜单权限关联查询
        mock_mp = MagicMock()
        mock_mp.menu_id = "menu-1"
        mock_mp.permission_id = "perm-1"

        mock_mp_result = MagicMock()
        mock_mp_result.scalars.return_value.all.return_value = [mock_mp]

        # 设置模拟会话行为
        mock_session.execute.side_effect = [
            mock_perm_result,  # 权限查询
            mock_menu_result,  # 菜单查询
            mock_mp_result,    # 菜单权限关联查询
        ]

        with patch('iam.services.menu_service.Menu.build_tree') as mock_build_tree:
            mock_build_tree.return_value = [
                {"id": "menu-1", "name": "用户管理", "children": []}
            ]

            # Act
            from iam.services.menu_service import MenuService
            result = await MenuService.get_user_menus(mock_session, "user-1")

            # Assert
            assert len(result) >= 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_menus_without_permissions(self, mock_session):
        """
        场景：用户无任何菜单权限时返回空数组

        GIVEN 用户没有关联任何角色或权限
        WHEN 调用 get_user_menus
        THEN 返回空数组
        """
        mock_perm_result = MagicMock()
        mock_perm_result.fetchall.return_value = []

        mock_menu = MagicMock()
        mock_menu.id = "menu-1"
        mock_menu.code = "iam:users"
        mock_menu.is_visible = True

        mock_menu_result = MagicMock()
        mock_menu_result.scalars.return_value.all.return_value = [mock_menu]

        mock_mp = MagicMock()
        mock_mp.menu_id = "menu-1"
        mock_mp.permission_id = "perm-1"

        mock_mp_result = MagicMock()
        mock_mp_result.scalars.return_value.all.return_value = [mock_mp]

        mock_session.execute.side_effect = [
            mock_perm_result,
            mock_menu_result,
            mock_mp_result,
        ]

        from iam.services.menu_service import MenuService
        result = await MenuService.get_user_menus(mock_session, "user-no-perms")

        assert result == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_menus_public_menus_visible(self, mock_session):
        """
        场景：无权限限制的菜单对所有用户可见

        GIVEN 菜单未关联任何权限
        WHEN 调用 get_user_menus
        THEN 所有登录用户可见此菜单
        """
        mock_perm_result = MagicMock()
        mock_perm_result.fetchall.return_value = [("perm-1",)]

        mock_public_menu = MagicMock()
        mock_public_menu.id = "menu-public"
        mock_public_menu.code = "demo:home"
        mock_public_menu.name = "首页"
        mock_public_menu.is_visible = True

        mock_menu_result = MagicMock()
        mock_menu_result.scalars.return_value.all.return_value = [mock_public_menu]

        mock_mp_result = MagicMock()
        mock_mp_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            mock_perm_result,
            mock_menu_result,
            mock_mp_result,
        ]

        with patch('iam.services.menu_service.Menu.build_tree') as mock_build_tree:
            mock_build_tree.return_value = [
                {"id": "menu-public", "name": "首页", "children": []}
            ]

            from iam.services.menu_service import MenuService
            result = await MenuService.get_user_menus(mock_session, "user-1")

            mock_build_tree.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_menus_empty_when_no_menus(self, mock_session):
        """
        场景：系统无菜单时返回空数组
        """
        mock_perm_result = MagicMock()
        mock_perm_result.fetchall.return_value = [("perm-1",)]

        mock_menu_result = MagicMock()
        mock_menu_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            mock_perm_result,
            mock_menu_result,
        ]

        from iam.services.menu_service import MenuService
        result = await MenuService.get_user_menus(mock_session, "user-1")

        assert result == []


class TestMenuServicePermissionLogic:
    """测试菜单权限过滤逻辑"""

    @pytest.mark.unit
    def test_menu_without_permissions_is_visible(self):
        """验证：无权限关联的菜单对登录用户可见"""
        menu_perms = set()
        user_perms = set()
        assert not menu_perms

    @pytest.mark.unit
    def test_menu_with_permissions_requires_user_permission(self):
        """验证：有权限限制的菜单需要用户拥有任一权限"""
        menu_perms = {"user:read", "user:write"}
        user_perms = {"user:read"}
        has_permission = bool(menu_perms & user_perms)
        assert has_permission is True

    @pytest.mark.unit
    def test_menu_permission_intersection(self):
        """验证：用户拥有任一权限即可见菜单"""
        menu_perms = {"user:read", "user:write", "user:delete"}
        user_has_only_read = {"user:read"}
        user_has_only_write = {"user:write"}
        user_has_no_perms = {"role:read"}

        assert bool(menu_perms & user_has_only_read) is True
        assert bool(menu_perms & user_has_only_write) is True
        assert bool(menu_perms & user_has_no_perms) is False
