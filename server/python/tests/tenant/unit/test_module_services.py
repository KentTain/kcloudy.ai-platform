"""
模块定义层服务单元测试
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tenant.services.module_menu_service import ModuleMenuService
from tenant.services.module_permission_service import ModulePermissionService
from tenant.services.module_role_service import ModuleRoleService
from tenant.services.module_service import ModuleService


class TestModuleService:
    """模块服务测试"""

    @pytest.mark.asyncio
    async def test_list_modules_with_keyword(self, session):
        """带关键词查询模块列表"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"
        mock_module.name = "演示模块"
        mock_module.is_active = True
        mock_module.created_at = datetime.now()

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_module]

        session.execute.side_effect = [count_result, list_result]

        items, total = await ModuleService.list_modules(
            session, page=1, page_size=20, keyword="演示"
        )

        assert len(items) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_by_id_returns_module(self, session):
        """根据 ID 获取模块"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_module
        session.execute.return_value = result

        module = await ModuleService.get_by_id(session, "module-1")

        assert module is mock_module

    @pytest.mark.asyncio
    async def test_get_by_code_returns_module(self, session):
        """根据编码获取模块"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_module
        session.execute.return_value = result

        module = await ModuleService.get_by_code(session, "demo")

        assert module is mock_module

    @pytest.mark.asyncio
    async def test_create_module_with_default_roles(self, session):
        """创建模块时自动创建默认角色"""
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        # 模拟 flush 后设置 module.id
        def set_id_side_effect(module):
            module.id = "module-1"

        session.add.side_effect = set_id_side_effect

        await ModuleService.create(
            session,
            code="demo",
            name="演示模块",
            description="测试用演示模块",
            is_active=True,
        )

        # 验证 add 被调用了 3 次：模块 + 2 个默认角色
        assert session.add.call_count == 3
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_module_success(self, session):
        """更新模块成功"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.name = "旧名称"

        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_module
        session.execute.return_value = result
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        module = await ModuleService.update(session, "module-1", name="新名称")

        assert module is mock_module
        assert module.name == "新名称"

    @pytest.mark.asyncio
    async def test_update_module_not_found(self, session):
        """更新不存在的模块返回 None"""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session.execute.return_value = result

        module = await ModuleService.update(session, "nonexistent", name="新名称")

        assert module is None

    @pytest.mark.asyncio
    async def test_delete_module_without_references(self, session):
        """无引用时删除模块成功"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        # 模块查询
        module_result = MagicMock()
        module_result.scalar_one_or_none.return_value = mock_module

        # 引用检查返回 0
        ref_result = MagicMock()
        ref_result.scalar.return_value = 0

        session.execute.side_effect = [module_result, ref_result]
        session.delete = AsyncMock()
        session.commit = AsyncMock()

        success = await ModuleService.delete(session, "module-1")

        assert success is True

    @pytest.mark.asyncio
    async def test_delete_module_with_tenant_module_references_raises_conflict(self, session):
        """模块被租户引用时删除抛出 ValueError"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        # 模块查询
        module_result = MagicMock()
        module_result.scalar_one_or_none.return_value = mock_module

        # 引用检查返回 3
        ref_result = MagicMock()
        ref_result.scalar.return_value = 3

        session.execute.side_effect = [module_result, ref_result]

        with pytest.raises(ValueError) as exc_info:
            await ModuleService.delete(session, "module-1")

        assert "3 个租户分配" in str(exc_info.value)


class TestModuleMenuService:
    """模块菜单服务测试"""

    @pytest.mark.asyncio
    async def test_list_menus(self, session):
        """查询模块菜单列表"""
        mock_menu1 = MagicMock()
        mock_menu1.id = "menu-1"
        mock_menu1.code = "dashboard"
        mock_menu1.tree_sort = 1
        mock_menu1.tree_level = 0
        mock_menu1.tree_leaf = True
        mock_menu1.parent_ids = "root,"

        mock_menu2 = MagicMock()
        mock_menu2.id = "menu-2"
        mock_menu2.code = "users"
        mock_menu2.parent_id = "menu-1"
        mock_menu2.tree_sort = 2
        mock_menu2.tree_level = 1
        mock_menu2.tree_leaf = True
        mock_menu2.parent_ids = "root,menu-1,"

        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_menu1, mock_menu2]
        session.execute.return_value = result

        menus = await ModuleMenuService.list_menus(session, "module-1")

        assert len(menus) == 2

    @pytest.mark.asyncio
    async def test_build_tree_structure(self):
        """构建菜单树形结构"""
        # 根菜单
        mock_menu1 = MagicMock()
        mock_menu1.id = "menu-1"
        mock_menu1.module_id = "module-1"
        mock_menu1.parent_id = None
        mock_menu1.code = "dashboard"
        mock_menu1.name = "仪表盘"
        mock_menu1.path = "/dashboard"
        mock_menu1.icon = "dashboard"
        mock_menu1.tree_sort = 1
        mock_menu1.tree_level = 0
        mock_menu1.tree_leaf = False
        mock_menu1.parent_ids = "root,"
        mock_menu1.tree_sorts = "00001,"
        mock_menu1.tree_names = "仪表盘"
        mock_menu1.is_visible = True
        mock_menu1.created_at = datetime.now()
        mock_menu1.updated_at = datetime.now()

        # 子菜单
        mock_menu2 = MagicMock()
        mock_menu2.id = "menu-2"
        mock_menu2.module_id = "module-1"
        mock_menu2.parent_id = "menu-1"
        mock_menu2.code = "users"
        mock_menu2.name = "用户管理"
        mock_menu2.path = "/dashboard/users"
        mock_menu2.icon = "user"
        mock_menu2.tree_sort = 1
        mock_menu2.tree_level = 1
        mock_menu2.tree_leaf = True
        mock_menu2.parent_ids = "root,menu-1,"
        mock_menu2.tree_sorts = "00001,00001,"
        mock_menu2.tree_names = "仪表盘/用户管理"
        mock_menu2.is_visible = True
        mock_menu2.created_at = datetime.now()
        mock_menu2.updated_at = datetime.now()

        tree = ModuleMenuService.build_tree([mock_menu1, mock_menu2])

        assert len(tree) == 1
        assert tree[0]["code"] == "dashboard"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["code"] == "users"

    @pytest.mark.asyncio
    async def test_create_menu_success(self, session):
        """创建菜单成功"""
        mock_publisher = AsyncMock()

        with patch("tenant.services.module_menu_service.event_publisher", mock_publisher):

            session.add = MagicMock()
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            # 模拟设置 menu.id
            def set_id_side_effect(menu):
                menu.id = "menu-1"

            session.add.side_effect = set_id_side_effect

            await ModuleMenuService.create(
                session,
                module_id="module-1",
                code="dashboard",
                name="仪表盘",
                path="/dashboard",
                tree_sort=1,
            )

        session.add.assert_called_once()
        mock_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_menu_success(self, session):
        """更新菜单成功"""
        mock_menu = MagicMock()
        mock_menu.id = "menu-1"
        mock_menu.name = "旧名称"
        mock_menu.module_id = "module-1"

        mock_publisher = AsyncMock()

        with patch("tenant.services.module_menu_service.event_publisher", mock_publisher):

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_menu
            session.execute.return_value = result
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            menu = await ModuleMenuService.update(session, "menu-1", name="新名称")

        assert menu is mock_menu
        assert menu.name == "新名称"
        mock_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_menu_self_parent_raises_error(self, session):
        """菜单不能以自己为父菜单"""
        mock_menu = MagicMock()
        mock_menu.id = "menu-1"

        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_menu
        session.execute.return_value = result

        with pytest.raises(ValueError) as exc_info:
            await ModuleMenuService.update(session, "menu-1", parent_id="menu-1")

        assert "不能以自己为父菜单" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_menu_with_children_raises_error(self, session):
        """有子菜单时删除抛出错误"""
        # 有 2 个子菜单
        child_result = MagicMock()
        child_result.scalar.return_value = 2
        session.execute.return_value = child_result

        with pytest.raises(ValueError) as exc_info:
            await ModuleMenuService.delete(session, "menu-1")

        assert "2 个子菜单" in str(exc_info.value)


class TestModulePermissionService:
    """模块权限服务测试"""

    @pytest.mark.asyncio
    async def test_list_permissions(self, session):
        """查询模块权限列表"""
        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        mock_perm.code = "user:read"
        mock_perm.resource = "user"
        mock_perm.action = "read"

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_perm]

        session.execute.side_effect = [count_result, list_result]

        items, total = await ModulePermissionService.list_permissions(session, "module-1")

        assert len(items) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_create_permission_success(self, session):
        """创建权限成功"""
        mock_publisher = AsyncMock()

        with patch("tenant.services.module_permission_service.event_publisher", mock_publisher):

            session.add = MagicMock()
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            def set_id_side_effect(perm):
                perm.id = "perm-1"

            session.add.side_effect = set_id_side_effect

            await ModulePermissionService.create(
                session,
                module_id="module-1",
                code="user:read",
                name="读取用户",
                resource="user",
                action="read",
            )

        session.add.assert_called_once()
        mock_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_permission_with_role_reference_raises_conflict(self, session):
        """权限被角色引用时删除抛出 ValueError"""
        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        mock_perm.code = "user:read"

        # 权限查询
        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = mock_perm

        # 角色引用检查返回 2
        ref_result = MagicMock()
        ref_result.scalar.return_value = 2

        session.execute.side_effect = [perm_result, ref_result]

        with pytest.raises(ValueError) as exc_info:
            await ModulePermissionService.delete(session, "perm-1")

        assert "2 个角色引用" in str(exc_info.value)


class TestModuleRoleService:
    """模块角色服务测试"""

    @pytest.mark.asyncio
    async def test_list_roles(self, session):
        """查询模块角色列表"""
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.code = "admin"
        mock_role.name = "管理员"
        mock_role.is_system = True

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_role]

        session.execute.side_effect = [count_result, list_result]

        items, total = await ModuleRoleService.list_roles(session, "module-1")

        assert len(items) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_create_role_success(self, session):
        """创建角色成功"""
        with patch("tenant.services.module_role_service.event_publisher") as mock_publisher:
            mock_publisher.publish = AsyncMock()

            session.add = MagicMock()
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            def set_id_side_effect(role):
                role.id = "role-1"

            session.add.side_effect = set_id_side_effect

            await ModuleRoleService.create(
                session,
                module_id="module-1",
                code="manager",
                name="经理",
                description="部门经理角色",
            )

        session.add.assert_called_once()
        mock_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_system_role_raises_error(self, session):
        """更新系统内置角色抛出错误"""
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.name = "系统管理员"
        mock_role.is_system = True

        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_role
        session.execute.return_value = result

        with pytest.raises(ValueError) as exc_info:
            await ModuleRoleService.update(session, "role-1", name="新名称")

        assert "系统内置角色" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_system_role_raises_error(self, session):
        """删除系统内置角色抛出错误"""
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.name = "系统管理员"
        mock_role.is_system = True

        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_role
        session.execute.return_value = result

        with pytest.raises(ValueError) as exc_info:
            await ModuleRoleService.delete(session, "role-1")

        assert "系统内置角色" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_non_system_role_success(self, session):
        """删除非系统角色成功"""
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.code = "manager"
        mock_role.name = "经理"
        mock_role.is_system = False
        mock_role.module_id = "module-1"

        with patch("tenant.services.module_role_service.event_publisher") as mock_publisher:
            mock_publisher.publish = AsyncMock()

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_role
            session.execute.return_value = result
            session.delete = AsyncMock()
            session.commit = AsyncMock()

            # 删除成功
            await ModuleRoleService.delete(session, "role-1")

        session.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_role_permissions(self, session):
        """更新角色权限关联"""
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.module_id = "module-1"
        mock_role.is_system = False  # 非系统角色才能修改权限

        with patch("tenant.services.module_role_service.event_publisher") as mock_publisher:
            mock_publisher.publish = AsyncMock()

            # 角色查询
            role_result = MagicMock()
            role_result.scalar_one_or_none.return_value = mock_role

            # 模块权限查询 - 返回权限对象字典
            mock_perm1 = MagicMock()
            mock_perm1.id = "perm-1"
            mock_perm2 = MagicMock()
            mock_perm2.id = "perm-2"

            perm_result = MagicMock()
            perm_result.scalars.return_value.all.return_value = [mock_perm1, mock_perm2]

            # 现有关联查询
            existing_result = MagicMock()
            existing_result.scalars.return_value.all.return_value = []

            session.execute.side_effect = [role_result, perm_result, existing_result]
            session.commit = AsyncMock()

            await ModuleRoleService.update_role_permissions(
                session,
                role_id="role-1",
                permission_ids=["perm-1", "perm-2"],
            )

        mock_publisher.publish.assert_called_once()
