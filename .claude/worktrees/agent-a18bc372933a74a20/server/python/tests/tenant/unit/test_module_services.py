"""
模块定义层服务单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from tenant.services.module_service import ModuleService
from tenant.services.module_menu_service import ModuleMenuService
from tenant.services.module_permission_service import ModulePermissionService
from tenant.services.module_role_service import ModuleRoleService
from framework.common.exceptions import ConflictError


class TestModuleService:
    """模块服务测试"""

    @pytest.mark.asyncio
    async def test_list_modules_with_keyword(self):
        """带关键词查询模块列表"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"
        mock_module.name = "演示模块"
        mock_module.is_active = True
        mock_module.created_at = datetime.now()

        with patch("tenant.services.module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            count_result = MagicMock()
            count_result.scalar.return_value = 1

            list_result = MagicMock()
            list_result.scalars.return_value.all.return_value = [mock_module]

            mock_ctx.execute.side_effect = [count_result, list_result]

            items, total = await ModuleService.list_modules(
                page=1, page_size=20, keyword="演示"
            )

        assert len(items) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_by_id_returns_module(self):
        """根据 ID 获取模块"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        with patch("tenant.services.module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_module
            mock_ctx.execute.return_value = result

            module = await ModuleService.get_by_id("module-1")

        assert module is mock_module

    @pytest.mark.asyncio
    async def test_get_by_code_returns_module(self):
        """根据编码获取模块"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        with patch("tenant.services.module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_module
            mock_ctx.execute.return_value = result

            module = await ModuleService.get_by_code("demo")

        assert module is mock_module

    @pytest.mark.asyncio
    async def test_create_module_with_default_roles(self):
        """创建模块时自动创建默认角色"""
        with patch("tenant.services.module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.add = MagicMock()
            mock_ctx.flush = AsyncMock()
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            # 模拟 flush 后设置 module.id
            def set_id_side_effect(module):
                module.id = "module-1"

            mock_ctx.add.side_effect = set_id_side_effect

            await ModuleService.create(
                code="demo",
                name="演示模块",
                description="测试用演示模块",
                is_active=True,
            )

        # 验证 add 被调用了 3 次：模块 + 2 个默认角色
        assert mock_ctx.add.call_count == 3
        mock_ctx.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_module_success(self):
        """更新模块成功"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.name = "旧名称"

        with patch("tenant.services.module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_module
            mock_ctx.execute.return_value = result
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            module = await ModuleService.update("module-1", name="新名称")

        assert module is mock_module
        assert module.name == "新名称"

    @pytest.mark.asyncio
    async def test_update_module_not_found(self):
        """更新不存在的模块返回 None"""
        with patch("tenant.services.module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            mock_ctx.execute.return_value = result

            module = await ModuleService.update("nonexistent", name="新名称")

        assert module is None

    @pytest.mark.asyncio
    async def test_delete_module_without_references(self):
        """无引用时删除模块成功"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        with patch("tenant.services.module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            # 模块查询
            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module

            # 引用检查返回 0
            ref_result = MagicMock()
            ref_result.scalar.return_value = 0

            mock_ctx.execute.side_effect = [module_result, ref_result]
            mock_ctx.delete = AsyncMock()
            mock_ctx.commit = AsyncMock()

            success = await ModuleService.delete("module-1")

        assert success is True

    @pytest.mark.asyncio
    async def test_delete_module_with_tenant_module_references_raises_conflict(self):
        """模块被租户引用时删除抛出 ValueError"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        with patch("tenant.services.module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            # 模块查询
            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module

            # 引用检查返回 3
            ref_result = MagicMock()
            ref_result.scalar.return_value = 3

            mock_ctx.execute.side_effect = [module_result, ref_result]

            with pytest.raises(ValueError) as exc_info:
                await ModuleService.delete("module-1")

            assert "3 个租户分配" in str(exc_info.value)


class TestModuleMenuService:
    """模块菜单服务测试"""

    @pytest.mark.asyncio
    async def test_list_menus(self):
        """查询模块菜单列表"""
        mock_menu1 = MagicMock()
        mock_menu1.id = "menu-1"
        mock_menu1.code = "dashboard"
        mock_menu1.sort_order = 1

        mock_menu2 = MagicMock()
        mock_menu2.id = "menu-2"
        mock_menu2.code = "users"
        mock_menu2.parent_id = "menu-1"
        mock_menu2.sort_order = 2

        with patch("tenant.services.module_menu_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalars.return_value.all.return_value = [mock_menu1, mock_menu2]
            mock_ctx.execute.return_value = result

            menus = await ModuleMenuService.list_menus("module-1")

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
        mock_menu1.sort_order = 1
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
        mock_menu2.sort_order = 1
        mock_menu2.is_visible = True
        mock_menu2.created_at = datetime.now()
        mock_menu2.updated_at = datetime.now()

        tree = ModuleMenuService.build_tree([mock_menu1, mock_menu2])

        assert len(tree) == 1
        assert tree[0]["code"] == "dashboard"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["code"] == "users"

    @pytest.mark.asyncio
    async def test_create_menu_success(self):
        """创建菜单成功"""
        mock_publisher = AsyncMock()

        with patch("tenant.services.module_menu_service.async_session") as mock_session, \
             patch("tenant.services.module_menu_service.event_publisher", mock_publisher):

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.add = MagicMock()
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            # 模拟设置 menu.id
            def set_id_side_effect(menu):
                menu.id = "menu-1"

            mock_ctx.add.side_effect = set_id_side_effect

            await ModuleMenuService.create(
                module_id="module-1",
                code="dashboard",
                name="仪表盘",
                path="/dashboard",
                sort_order=1,
            )

        mock_ctx.add.assert_called_once()
        mock_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_menu_success(self):
        """更新菜单成功"""
        mock_menu = MagicMock()
        mock_menu.id = "menu-1"
        mock_menu.name = "旧名称"
        mock_menu.module_id = "module-1"

        mock_publisher = AsyncMock()

        with patch("tenant.services.module_menu_service.async_session") as mock_session, \
             patch("tenant.services.module_menu_service.event_publisher", mock_publisher):

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_menu
            mock_ctx.execute.return_value = result
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            menu = await ModuleMenuService.update("menu-1", name="新名称")

        assert menu is mock_menu
        assert menu.name == "新名称"
        mock_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_menu_self_parent_raises_error(self):
        """菜单不能以自己为父菜单"""
        mock_menu = MagicMock()
        mock_menu.id = "menu-1"

        with patch("tenant.services.module_menu_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_menu
            mock_ctx.execute.return_value = result

            with pytest.raises(ValueError) as exc_info:
                await ModuleMenuService.update("menu-1", parent_id="menu-1")

            assert "不能以自己为父菜单" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_menu_with_children_raises_error(self):
        """有子菜单时删除抛出错误"""
        with patch("tenant.services.module_menu_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            # 有 2 个子菜单
            child_result = MagicMock()
            child_result.scalar.return_value = 2
            mock_ctx.execute.return_value = child_result

            with pytest.raises(ValueError) as exc_info:
                await ModuleMenuService.delete("menu-1")

            assert "2 个子菜单" in str(exc_info.value)


class TestModulePermissionService:
    """模块权限服务测试"""

    @pytest.mark.asyncio
    async def test_list_permissions(self):
        """查询模块权限列表"""
        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        mock_perm.code = "user:read"
        mock_perm.resource = "user"
        mock_perm.action = "read"

        with patch("tenant.services.module_permission_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            count_result = MagicMock()
            count_result.scalar.return_value = 1

            list_result = MagicMock()
            list_result.scalars.return_value.all.return_value = [mock_perm]

            mock_ctx.execute.side_effect = [count_result, list_result]

            items, total = await ModulePermissionService.list_permissions("module-1")

        assert len(items) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_create_permission_success(self):
        """创建权限成功"""
        mock_publisher = AsyncMock()

        with patch("tenant.services.module_permission_service.async_session") as mock_session, \
             patch("tenant.services.module_permission_service.event_publisher", mock_publisher):

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.add = MagicMock()
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            def set_id_side_effect(perm):
                perm.id = "perm-1"

            mock_ctx.add.side_effect = set_id_side_effect

            await ModulePermissionService.create(
                module_id="module-1",
                code="user:read",
                name="读取用户",
                resource="user",
                action="read",
            )

        mock_ctx.add.assert_called_once()
        mock_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_permission_with_role_reference_raises_conflict(self):
        """权限被角色引用时删除抛出 ValueError"""
        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        mock_perm.code = "user:read"

        with patch("tenant.services.module_permission_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            # 权限查询
            perm_result = MagicMock()
            perm_result.scalar_one_or_none.return_value = mock_perm

            # 角色引用检查返回 2
            ref_result = MagicMock()
            ref_result.scalar.return_value = 2

            mock_ctx.execute.side_effect = [perm_result, ref_result]

            with pytest.raises(ValueError) as exc_info:
                await ModulePermissionService.delete("perm-1")

            assert "2 个角色引用" in str(exc_info.value)


class TestModuleRoleService:
    """模块角色服务测试"""

    @pytest.mark.asyncio
    async def test_list_roles(self):
        """查询模块角色列表"""
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.code = "admin"
        mock_role.name = "管理员"
        mock_role.is_system = True

        with patch("tenant.services.module_role_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            count_result = MagicMock()
            count_result.scalar.return_value = 1

            list_result = MagicMock()
            list_result.scalars.return_value.all.return_value = [mock_role]

            mock_ctx.execute.side_effect = [count_result, list_result]

            items, total = await ModuleRoleService.list_roles("module-1")

        assert len(items) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_create_role_success(self):
        """创建角色成功"""
        with patch("tenant.services.module_role_service.async_session") as mock_session, \
             patch("tenant.services.module_role_service.event_publisher") as mock_publisher:
            mock_publisher.publish = AsyncMock()

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.add = MagicMock()
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            def set_id_side_effect(role):
                role.id = "role-1"

            mock_ctx.add.side_effect = set_id_side_effect

            await ModuleRoleService.create(
                module_id="module-1",
                code="manager",
                name="经理",
                description="部门经理角色",
            )

        mock_ctx.add.assert_called_once()
        mock_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_system_role_raises_error(self):
        """更新系统内置角色抛出错误"""
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.name = "系统管理员"
        mock_role.is_system = True

        with patch("tenant.services.module_role_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_role
            mock_ctx.execute.return_value = result

            with pytest.raises(ValueError) as exc_info:
                await ModuleRoleService.update("role-1", name="新名称")

            assert "系统内置角色" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_system_role_raises_error(self):
        """删除系统内置角色抛出错误"""
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.name = "系统管理员"
        mock_role.is_system = True

        with patch("tenant.services.module_role_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_role
            mock_ctx.execute.return_value = result

            with pytest.raises(ValueError) as exc_info:
                await ModuleRoleService.delete("role-1")

            assert "系统内置角色" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_non_system_role_success(self):
        """删除非系统角色成功"""
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.code = "manager"
        mock_role.name = "经理"
        mock_role.is_system = False
        mock_role.module_id = "module-1"

        with patch("tenant.services.module_role_service.async_session") as mock_session, \
             patch("tenant.services.module_role_service.event_publisher") as mock_publisher:
            mock_publisher.publish = AsyncMock()

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_role
            mock_ctx.execute.return_value = result
            mock_ctx.delete = AsyncMock()
            mock_ctx.commit = AsyncMock()

            # 删除成功
            await ModuleRoleService.delete("role-1")

        mock_ctx.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_role_permissions(self):
        """更新角色权限关联"""
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.module_id = "module-1"
        mock_role.is_system = False  # 非系统角色才能修改权限

        with patch("tenant.services.module_role_service.async_session") as mock_session, \
             patch("tenant.services.module_role_service.event_publisher") as mock_publisher:
            mock_publisher.publish = AsyncMock()

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

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

            mock_ctx.execute.side_effect = [role_result, perm_result, existing_result]
            mock_ctx.commit = AsyncMock()

            await ModuleRoleService.update_role_permissions(
                role_id="role-1",
                permission_ids=["perm-1", "perm-2"],
            )

        mock_publisher.publish.assert_called_once()
