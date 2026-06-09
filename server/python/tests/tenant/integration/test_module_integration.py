"""
租户模块系统集成测试

测试完整的模块分配流程：
1. 创建模块
2. 定义菜单/权限/角色
3. 租户分配模块
4. 验证同步结果
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from tenant.services.module_service import ModuleService
from tenant.services.module_menu_service import ModuleMenuService
from tenant.services.module_permission_service import ModulePermissionService
from tenant.services.module_role_service import ModuleRoleService
from tenant.services.tenant_module_service import TenantModuleService
from iam.services.module_sync_service import ModuleSyncService
from framework.events.domain_events import (
    ModuleAssigned,
    ModuleUnassigned,
    ModuleMenuCreated,
    ModuleRoleCreated,
)


class TestModuleAssignmentIntegration:
    """模块分配集成测试"""

    @pytest.mark.asyncio
    async def test_complete_module_assignment_flow(self):
        """
        完整模块分配流程测试

        流程：
        1. 创建模块（自动创建默认角色）
        2. 创建菜单
        3. 创建权限
        4. 更新角色权限关联
        5. 租户分配模块
        6. 验证同步结果
        """
        # 模拟数据库会话
        mock_session = AsyncMock()

        # ========== 1. 创建模块 ==========
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"
        mock_module.name = "演示模块"
        mock_module.is_active = True
        mock_module.is_need = False

        # ========== 2. 模块菜单 ==========
        mock_menu = MagicMock()
        mock_menu.id = "menu-1"
        mock_menu.module_id = "module-1"
        mock_menu.parent_id = None
        mock_menu.code = "dashboard"
        mock_menu.name = "仪表盘"
        mock_menu.path = "/dashboard"
        mock_menu.icon = "dashboard"
        mock_menu.is_visible = True

        # ========== 3. 模块权限 ==========
        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        mock_perm.code = "user:read"
        mock_perm.name = "读取用户"
        mock_perm.resource = "user"
        mock_perm.action = "read"
        mock_perm.description = None

        # ========== 4. 模块角色 ==========
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.code = "admin"
        mock_role.name = "管理员"
        mock_role.description = "系统管理员"
        mock_role.is_system = True

        # ========== 5. 角色权限关联 ==========
        mock_role_perm = MagicMock()
        mock_role_perm.module_role_id = "role-1"
        mock_role_perm.module_permission_id = "perm-1"

        # 设置查询返回
        menu_result = MagicMock()
        menu_result.scalars.return_value.all.return_value = [mock_menu]

        perm_result = MagicMock()
        perm_result.scalars.return_value.all.return_value = [mock_perm]

        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = [mock_role]

        role_perm_result = MagicMock()
        role_perm_result.scalars.return_value.all.return_value = [mock_role_perm]

        mock_session.execute.side_effect = [
            menu_result,
            perm_result,
            role_result,
            role_perm_result,
        ]
        mock_session.flush = AsyncMock()

        # ========== 6. 同步模块分配 ==========
        await ModuleSyncService.sync_module_assigned(
            mock_session, "tenant-1", "module-1", "demo"
        )

        # 验证创建了菜单、权限、角色
        assert mock_session.add.call_count >= 3

    @pytest.mark.asyncio
    async def test_module_unassignment_flow(self):
        """
        模块取消分配流程测试

        流程：
        1. 查询模块定义层数据
        2. 查询租户实例层数据
        3. 按依赖顺序删除
        """
        mock_session = AsyncMock()

        # 模拟模块角色 ID
        role_result = MagicMock()
        role_result.all.return_value = [("role-1",)]

        # 模拟模块权限 ID
        perm_result = MagicMock()
        perm_result.all.return_value = [("perm-1",)]

        # 模拟模块菜单 ID
        menu_result = MagicMock()
        menu_result.all.return_value = [("menu-1",)]

        # 模拟租户角色
        tenant_role_result = MagicMock()
        tenant_role_result.all.return_value = [("tenant-role-1",)]

        # 模拟租户权限
        tenant_perm_result = MagicMock()
        tenant_perm_result.all.return_value = [("tenant-perm-1",)]

        # 模拟租户菜单
        tenant_menu_result = MagicMock()
        tenant_menu_result.all.return_value = [("tenant-menu-1",)]

        mock_session.execute.side_effect = [
            role_result,
            perm_result,
            menu_result,
            tenant_role_result,
            tenant_perm_result,
            tenant_menu_result,
        ]

        await ModuleSyncService.sync_module_unassigned(
            mock_session, "tenant-1", "module-1"
        )

        # 验证执行了删除操作
        assert mock_session.execute.call_count >= 6

    @pytest.mark.asyncio
    async def test_incremental_menu_sync(self):
        """
        增量菜单同步测试

        场景：模块已分配给租户，新增菜单后同步
        """
        mock_session = AsyncMock()

        # 模拟模块
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        # 模拟新菜单
        mock_menu = MagicMock()
        mock_menu.id = "menu-2"
        mock_menu.module_id = "module-1"
        mock_menu.parent_id = "menu-1"
        mock_menu.code = "users"
        mock_menu.name = "用户管理"
        mock_menu.path = "/dashboard/users"
        mock_menu.icon = "user"
        mock_menu.is_visible = True

        # 模拟已分配租户
        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        # 模拟父菜单
        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = "tenant-menu-1"

        module_result = MagicMock()
        module_result.scalar_one_or_none.return_value = mock_module

        menu_result = MagicMock()
        menu_result.scalar_one_or_none.return_value = mock_menu

        mock_session.execute.side_effect = [
            module_result,
            menu_result,
            tm_result,
            parent_result,
        ]

        await ModuleSyncService.sync_module_menu_created(
            mock_session, "menu-2", "module-1"
        )

        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_incremental_permission_sync(self):
        """
        增量权限同步测试

        场景：模块已分配给租户，新增权限后同步
        """
        mock_session = AsyncMock()

        # 模拟新权限
        mock_perm = MagicMock()
        mock_perm.id = "perm-2"
        mock_perm.code = "user:write"
        mock_perm.name = "编辑用户"
        mock_perm.resource = "user"
        mock_perm.action = "write"
        mock_perm.description = None

        # 模拟已分配租户
        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = mock_perm

        mock_session.execute.side_effect = [perm_result, tm_result]

        await ModuleSyncService.sync_module_permission_created(
            mock_session, "perm-2", "module-1"
        )

        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_incremental_role_sync(self):
        """
        增量角色同步测试

        场景：模块已分配给租户，新增角色后同步
        """
        mock_session = AsyncMock()

        # 模拟新角色
        mock_role = MagicMock()
        mock_role.id = "role-2"
        mock_role.code = "manager"
        mock_role.name = "经理"
        mock_role.description = "部门经理"
        mock_role.is_system = False

        # 模拟已分配租户
        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = mock_role

        mock_session.execute.side_effect = [role_result, tm_result]

        await ModuleSyncService.sync_module_role_created(
            mock_session, "role-2", "module-1"
        )

        mock_session.add.assert_called_once()


class TestEventDrivenSync:
    """事件驱动同步测试"""

    @pytest.mark.asyncio
    async def test_module_assignment_triggers_sync(self):
        """模块分配触发同步"""
        with patch("tenant.services.tenant_module_service.event_publisher") as mock_publisher:
            mock_module = MagicMock()
            mock_module.id = "module-1"
            mock_module.code = "demo"
            mock_module.is_active = True
            mock_module.is_need = False

            with patch("tenant.services.tenant_module_service.async_session") as mock_session:
                mock_ctx = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_ctx

                module_result = MagicMock()
                module_result.scalar_one_or_none.return_value = mock_module

                existing_result = MagicMock()
                existing_result.scalar_one_or_none.return_value = None

                mock_ctx.execute.side_effect = [module_result, existing_result]
                mock_ctx.add = MagicMock()
                mock_ctx.commit = AsyncMock()
                mock_ctx.refresh = AsyncMock()

                await TenantModuleService.assign_module(
                    tenant_id="tenant-1",
                    module_id="module-1",
                    started_at=datetime.now(),
                )

            # 验证发布了 ModuleAssigned 事件
            mock_publisher.publish.assert_called_once()
            event = mock_publisher.publish.call_args[0][0]
            assert isinstance(event, ModuleAssigned)
            assert event.tenant_id == "tenant-1"
            assert event.module_id == "module-1"

    @pytest.mark.asyncio
    async def test_menu_creation_triggers_sync(self):
        """菜单创建触发同步"""
        with patch("tenant.services.module_menu_service.event_publisher") as mock_publisher:
            with patch("tenant.services.module_menu_service.async_session") as mock_session:
                mock_ctx = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_ctx
                mock_ctx.add = MagicMock()
                mock_ctx.commit = AsyncMock()
                mock_ctx.refresh = AsyncMock()

                def set_id(menu):
                    menu.id = "menu-1"

                mock_ctx.add.side_effect = set_id

                await ModuleMenuService.create(
                    module_id="module-1",
                    code="dashboard",
                    name="仪表盘",
                    path="/dashboard",
                )

            # 验证发布了 ModuleMenuCreated 事件
            mock_publisher.publish.assert_called_once()
            event = mock_publisher.publish.call_args[0][0]
            assert isinstance(event, ModuleMenuCreated)

    @pytest.mark.asyncio
    async def test_role_creation_triggers_sync(self):
        """角色创建触发同步"""
        with patch("tenant.services.module_role_service.event_publisher") as mock_publisher:
            with patch("tenant.services.module_role_service.async_session") as mock_session:
                mock_ctx = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_ctx
                mock_ctx.add = MagicMock()
                mock_ctx.commit = AsyncMock()
                mock_ctx.refresh = AsyncMock()

                def set_id(role):
                    role.id = "role-1"

                mock_ctx.add.side_effect = set_id

                await ModuleRoleService.create(
                    module_id="module-1",
                    code="manager",
                    name="经理",
                )

            # 验证发布了 ModuleRoleCreated 事件
            mock_publisher.publish.assert_called_once()
            event = mock_publisher.publish.call_args[0][0]
            assert isinstance(event, ModuleRoleCreated)


class TestBoundaryConditions:
    """边界条件测试"""

    @pytest.mark.asyncio
    async def test_sync_module_with_no_menus(self):
        """同步无菜单的模块"""
        mock_session = AsyncMock()

        # 无菜单
        menu_result = MagicMock()
        menu_result.scalars.return_value.all.return_value = []

        # 有权限
        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        perm_result = MagicMock()
        perm_result.scalars.return_value.all.return_value = [mock_perm]

        # 有角色
        mock_role = MagicMock()
        mock_role.id = "role-1"
        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = [mock_role]

        role_perm_result = MagicMock()
        role_perm_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            menu_result,
            perm_result,
            role_result,
            role_perm_result,
        ]
        mock_session.flush = AsyncMock()

        await ModuleSyncService.sync_module_assigned(
            mock_session, "tenant-1", "module-1", "demo"
        )

        # 应该只创建权限和角色
        assert mock_session.add.call_count >= 2

    @pytest.mark.asyncio
    async def test_sync_module_with_no_permissions(self):
        """同步无权限的模块"""
        mock_session = AsyncMock()

        # 有菜单
        mock_menu = MagicMock()
        mock_menu.id = "menu-1"
        mock_menu.parent_id = None
        menu_result = MagicMock()
        menu_result.scalars.return_value.all.return_value = [mock_menu]

        # 无权限
        perm_result = MagicMock()
        perm_result.scalars.return_value.all.return_value = []

        # 有角色
        mock_role = MagicMock()
        mock_role.id = "role-1"
        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = [mock_role]

        role_perm_result = MagicMock()
        role_perm_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            menu_result,
            perm_result,
            role_result,
            role_perm_result,
        ]
        mock_session.flush = AsyncMock()

        await ModuleSyncService.sync_module_assigned(
            mock_session, "tenant-1", "module-1", "demo"
        )

        # 应该只创建菜单和角色
        assert mock_session.add.call_count >= 2

    @pytest.mark.asyncio
    async def test_sync_to_multiple_tenants(self):
        """同步到多个租户"""
        mock_session = AsyncMock()

        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        mock_perm.code = "user:read"
        mock_perm.name = "读取用户"
        mock_perm.resource = "user"
        mock_perm.action = "read"
        mock_perm.description = None

        # 多个租户
        tm_result = MagicMock()
        tm_result.all.return_value = [
            ("tenant-1",),
            ("tenant-2",),
            ("tenant-3",),
        ]

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = mock_perm

        mock_session.execute.side_effect = [perm_result, tm_result]

        await ModuleSyncService.sync_module_permission_created(
            mock_session, "perm-1", "module-1"
        )

        # 应该为 3 个租户分别创建权限
        assert mock_session.add.call_count == 3

    @pytest.mark.asyncio
    async def test_sync_nested_menu_structure(self):
        """同步嵌套菜单结构"""
        mock_session = AsyncMock()

        # 父菜单
        mock_parent = MagicMock()
        mock_parent.id = "menu-1"
        mock_parent.parent_id = None
        mock_parent.code = "dashboard"
        mock_parent.name = "仪表盘"
        mock_parent.path = "/dashboard"
        mock_parent.icon = "dashboard"
        mock_parent.is_visible = True

        # 子菜单
        mock_child = MagicMock()
        mock_child.id = "menu-2"
        mock_child.parent_id = "menu-1"
        mock_child.code = "users"
        mock_child.name = "用户管理"
        mock_child.path = "/dashboard/users"
        mock_child.icon = "user"
        mock_child.is_visible = True

        # 按层级排序后的列表
        menu_result = MagicMock()
        menu_result.scalars.return_value.all.return_value = [mock_parent, mock_child]

        perm_result = MagicMock()
        perm_result.scalars.return_value.all.return_value = []

        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [menu_result, perm_result, role_result]
        mock_session.flush = AsyncMock()

        # 模拟第二次 flush 后获取 menu.id
        call_count = 0

        def mock_flush():
            nonlocal call_count
            call_count += 1

        mock_session.flush = AsyncMock(side_effect=mock_flush)

        await ModuleSyncService.sync_module_assigned(
            mock_session, "tenant-1", "module-1", "demo"
        )

        # 应该创建 2 个菜单
        assert mock_session.add.call_count >= 2
