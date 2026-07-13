"""
租户模块系统集成测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from iam.services.module_sync_service import ModuleSyncService


class TestModuleAssignmentIntegration:
    """模块分配集成测试"""

    @pytest.mark.asyncio
    async def test_complete_module_assignment_flow(self):
        """完整模块分配流程测试"""
        mock_session = AsyncMock()

        mock_menu = MagicMock()
        mock_menu.id = "menu-1"
        mock_menu.module_id = "module-1"
        mock_menu.parent_id = None
        mock_menu.code = "dashboard"
        mock_menu.name = "仪表盘"
        mock_menu.path = "/dashboard"
        mock_menu.icon = "dashboard"
        mock_menu.is_visible = True
        mock_menu.tree_sort = 0
        mock_menu.tree_level = 0
        mock_menu.tree_leaf = True
        mock_menu.parent_ids = "root,"
        mock_menu.tree_sorts = "00000,"
        mock_menu.tree_names = "仪表盘"

        menu_result = MagicMock()
        menu_result.scalars.return_value.all.return_value = [mock_menu]

        mock_permission = MagicMock()
        mock_permission.id = "perm-1"
        mock_permission.module_id = "module-1"
        mock_permission.code = "demo:dashboard:read"
        mock_permission.name = "查看仪表盘"
        mock_permission.resource = "dashboard"
        mock_permission.action = "read"

        perm_result = MagicMock()
        perm_result.scalars.return_value.all.return_value = [mock_permission]

        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.module_id = "module-1"
        mock_role.code = "admin"
        mock_role.name = "管理员"
        mock_role.is_system = True

        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = [mock_role]

        mrp_result = MagicMock()
        mrp_result.scalars.return_value.all.return_value = []

        # 空的已存在检查结果（首次同步没有历史数据）
        empty_existing = MagicMock()
        empty_existing.scalars.return_value.all.return_value = []

        # 提供充足的 side_effect 条目（sync_module_assigned 含大量 execute 调用）
        mock_session.execute.side_effect = (
            [menu_result, perm_result, role_result, mrp_result]
            + [empty_existing] * 50  # 幂等检查、树操作、全局角色同步等
        )

        await ModuleSyncService.sync_module_assigned(
            mock_session, "tenant-1", "module-1", "demo"
        )

        assert mock_session.add.call_count >= 3

    @pytest.mark.asyncio
    async def test_module_unassignment_flow(self):
        """模块取消分配流程测试"""
        mock_session = AsyncMock()

        role_result = MagicMock()
        role_result.all.return_value = [("role-1",)]

        perm_result = MagicMock()
        perm_result.all.return_value = [("perm-1",)]

        menu_result = MagicMock()
        menu_result.all.return_value = [("menu-1",)]

        tenant_role_result = MagicMock()
        tenant_role_result.all.return_value = [("tenant-role-1",)]

        tenant_perm_result = MagicMock()
        tenant_perm_result.all.return_value = [("tenant-perm-1",)]

        tenant_menu_result = MagicMock()
        tenant_menu_result.all.return_value = [("tenant-menu-1",)]

        delete_result = MagicMock()

        child_result = MagicMock()
        child_result.all.return_value = []

        mock_session.execute.side_effect = [
            role_result,
            perm_result,
            menu_result,
            tenant_role_result,
            tenant_perm_result,
            tenant_menu_result,
            delete_result,
            delete_result,
            delete_result,
            child_result,
            delete_result,
        ]

        await ModuleSyncService.sync_module_unassigned(
            mock_session, "tenant-1", "module-1"
        )

        assert mock_session.execute.call_count == 11

    @pytest.mark.asyncio
    async def test_incremental_menu_sync(self):
        """增量菜单同步测试"""
        mock_session = AsyncMock()

        module_result = MagicMock()
        module_result.scalar_one_or_none.return_value = MagicMock(code="demo")

        menu_result = MagicMock()
        menu_result.scalar_one_or_none.return_value = MagicMock(
            id="menu-2",
            module_id="module-1",
            parent_id="menu-1",
            code="users",
            name="用户管理",
            path="/dashboard/users",
            icon="user",
            is_visible=True,
        )

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = "tenant-menu-1"

        mock_session.execute.side_effect = [
            module_result,
            menu_result,
            tm_result,
            parent_result,
        ] + [MagicMock()] * 20  # Menu.create_node 内部树操作

        await ModuleSyncService.sync_module_menu_created(
            mock_session, "menu-2", "module-1"
        )
        assert mock_session.add.call_count >= 1

    @pytest.mark.asyncio
    async def test_incremental_permission_sync(self):
        """增量权限同步测试"""
        mock_session = AsyncMock()

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = MagicMock(
            id="perm-2",
            module_id="module-1",
            code="demo:users:write",
            name="编辑用户",
            resource="users",
            action="write",
            description="编辑用户权限",
        )

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        mock_session.execute.side_effect = [
            perm_result,
            tm_result,
        ]

        await ModuleSyncService.sync_module_permission_created(
            mock_session, "perm-2", "module-1"
        )
        assert mock_session.add.call_count >= 1

    @pytest.mark.asyncio
    async def test_incremental_role_sync(self):
        """增量角色同步测试"""
        mock_session = AsyncMock()

        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = MagicMock(
            id="role-2",
            module_id="module-1",
            code="operator",
            name="操作员",
            is_system=False,
            description="操作员角色",
        )

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        mock_session.execute.side_effect = [
            role_result,
            tm_result,
        ]

        await ModuleSyncService.sync_module_role_created(
            mock_session, "role-2", "module-1"
        )
        assert mock_session.add.call_count >= 1

    @pytest.mark.asyncio
    async def test_role_permission_change_sync(self):
        """角色权限变更同步测试"""
        mock_session = AsyncMock()

        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = MagicMock(
            module_id="module-1"
        )

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        tenant_role_result = MagicMock()
        tenant_role_result.scalar_one_or_none.return_value = "tenant-role-1"

        tenant_perm_result = MagicMock()
        tenant_perm_result.all.return_value = [("tenant-perm-1",), ("tenant-perm-2",)]

        mock_session.execute.side_effect = [
            role_result,
            tm_result,
            tenant_role_result,
            tenant_perm_result,
        ]

        await ModuleSyncService.sync_module_role_permission_changed(
            mock_session, "role-1", ["perm-1", "perm-2"]
        )
        assert mock_session.execute.call_count >= 4
