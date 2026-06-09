"""
IAM 模块同步服务单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from iam.services.module_sync_service import ModuleSyncService
from iam.listeners.handlers.event_handler import (
    ModuleAssignedHandler,
    ModuleUnassignedHandler,
    ModuleMenuCreatedHandler,
    ModuleMenuUpdatedHandler,
    ModuleMenuDeletedHandler,
    ModulePermissionCreatedHandler,
    ModulePermissionUpdatedHandler,
    ModulePermissionDeletedHandler,
    ModuleRoleCreatedHandler,
    ModuleRoleUpdatedHandler,
    ModuleRoleDeletedHandler,
    ModuleRolePermissionChangedHandler,
)
from framework.events.base import EventStream


class TestModuleSyncService:
    """模块同步服务测试"""

    @pytest.mark.asyncio
    async def test_sync_module_assigned(self):
        """同步模块分配事件"""
        mock_session = AsyncMock()

        # 模拟模块菜单
        mock_menu = MagicMock()
        mock_menu.id = "menu-1"
        mock_menu.module_id = "module-1"
        mock_menu.parent_id = None
        mock_menu.code = "dashboard"
        mock_menu.name = "仪表盘"
        mock_menu.path = "/dashboard"
        mock_menu.icon = "dashboard"
        mock_menu.is_visible = True

        # 模拟模块权限
        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        mock_perm.code = "user:read"
        mock_perm.name = "读取用户"
        mock_perm.resource = "user"
        mock_perm.action = "read"
        mock_perm.description = "读取用户权限"

        # 模拟模块角色
        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.code = "admin"
        mock_role.name = "管理员"
        mock_role.description = "系统管理员"
        mock_role.is_system = True

        # 模拟角色权限关联
        mock_role_perm = MagicMock()
        mock_role_perm.module_role_id = "role-1"
        mock_role_perm.module_permission_id = "perm-1"

        # 设置查询返回结果
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

        await ModuleSyncService.sync_module_assigned(
            mock_session, "tenant-1", "module-1", "demo"
        )

        # 验证创建了菜单、权限、角色
        assert mock_session.add.call_count >= 3  # 至少 3 次（菜单、权限、角色）

    @pytest.mark.asyncio
    async def test_sync_module_unassigned(self):
        """同步模块取消分配事件"""
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
    async def test_sync_module_menu_created(self):
        """同步模块菜单创建事件"""
        mock_session = AsyncMock()

        # 模拟模块
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        # 模拟模块菜单
        mock_menu = MagicMock()
        mock_menu.id = "menu-1"
        mock_menu.module_id = "module-1"
        mock_menu.parent_id = None
        mock_menu.code = "dashboard"
        mock_menu.name = "仪表盘"
        mock_menu.path = "/dashboard"
        mock_menu.icon = "dashboard"
        mock_menu.is_visible = True

        # 模拟已分配租户
        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        module_result = MagicMock()
        module_result.scalar_one_or_none.return_value = mock_module

        menu_result = MagicMock()
        menu_result.scalar_one_or_none.return_value = mock_menu

        mock_session.execute.side_effect = [module_result, menu_result, tm_result]

        await ModuleSyncService.sync_module_menu_created(
            mock_session, "menu-1", "module-1"
        )

        mock_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_sync_module_permission_created(self):
        """同步模块权限创建事件"""
        mock_session = AsyncMock()

        # 模拟模块权限
        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        mock_perm.code = "user:read"
        mock_perm.name = "读取用户"
        mock_perm.resource = "user"
        mock_perm.action = "read"
        mock_perm.description = None

        # 模拟已分配租户
        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = mock_perm

        mock_session.execute.side_effect = [perm_result, tm_result]

        await ModuleSyncService.sync_module_permission_created(
            mock_session, "perm-1", "module-1"
        )

        mock_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_sync_module_role_created(self):
        """同步模块角色创建事件"""
        mock_session = AsyncMock()

        # 模拟模块角色
        mock_role = MagicMock()
        mock_role.id = "role-1"
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
            mock_session, "role-1", "module-1"
        )

        mock_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_sync_module_role_permission_changed(self):
        """同步模块角色权限变更事件"""
        mock_session = AsyncMock()

        # 模拟角色权限关联
        mrp_result = MagicMock()
        mrp_result.all.return_value = [("perm-1",)]

        # 模拟已分配租户
        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        # 模拟租户角色
        tenant_role_result = MagicMock()
        tenant_role_result.scalar_one_or_none.return_value = "tenant-role-1"

        # 模拟租户权限
        tenant_perm_result = MagicMock()
        tenant_perm_result.scalar_one_or_none.return_value = "tenant-perm-1"

        mock_session.execute.side_effect = [
            mrp_result,
            tm_result,
            tenant_role_result,
            tenant_perm_result,
        ]

        await ModuleSyncService.sync_module_role_permission_changed(
            mock_session, "role-1", "module-1"
        )

        # 验证删除了旧的角色权限关联并创建了新的
        assert mock_session.execute.call_count >= 4


class TestModuleAssignedHandler:
    """模块分配事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块分配事件"""
        handler = ModuleAssignedHandler()

        message = {
            "data": json.dumps({
                "tenant_id": "tenant-1",
                "module_id": "module-1",
            })
        }

        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session, \
             patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module
            mock_ctx.execute.return_value = module_result
            mock_ctx.commit = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_assigned.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_missing_fields(self):
        """缺少必要字段时跳过"""
        handler = ModuleAssignedHandler()

        message = {
            "data": json.dumps({
                "tenant_id": "tenant-1",
                # 缺少 module_id
            })
        }

        # 不应抛出异常，只是记录警告
        await handler.handle(message)

    @pytest.mark.asyncio
    async def test_handle_module_not_found(self):
        """模块不存在时跳过"""
        handler = ModuleAssignedHandler()

        message = {
            "data": json.dumps({
                "tenant_id": "tenant-1",
                "module_id": "nonexistent",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = None
            mock_ctx.execute.return_value = module_result

            await handler.handle(message)

        # 不应抛出异常


class TestModuleUnassignedHandler:
    """模块取消分配事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块取消分配事件"""
        handler = ModuleUnassignedHandler()

        message = {
            "data": json.dumps({
                "tenant_id": "tenant-1",
                "module_id": "module-1",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session, \
             patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_unassigned.assert_awaited_once()


class TestModuleMenuCreatedHandler:
    """模块菜单创建事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块菜单创建事件"""
        handler = ModuleMenuCreatedHandler()

        message = {
            "data": json.dumps({
                "module_menu_id": "menu-1",
                "module_id": "module-1",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session, \
             patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_menu_created.assert_awaited_once()


class TestModulePermissionCreatedHandler:
    """模块权限创建事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块权限创建事件"""
        handler = ModulePermissionCreatedHandler()

        message = {
            "data": json.dumps({
                "module_permission_id": "perm-1",
                "module_id": "module-1",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session, \
             patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_permission_created.assert_awaited_once()


class TestModuleRoleCreatedHandler:
    """模块角色创建事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块角色创建事件"""
        handler = ModuleRoleCreatedHandler()

        message = {
            "data": json.dumps({
                "module_role_id": "role-1",
                "module_id": "module-1",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session, \
             patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_role_created.assert_awaited_once()


class TestModuleRolePermissionChangedHandler:
    """模块角色权限变更事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块角色权限变更事件"""
        handler = ModuleRolePermissionChangedHandler()

        message = {
            "data": json.dumps({
                "module_role_id": "role-1",
                "module_id": "module-1",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session, \
             patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_role_permission_changed.assert_awaited_once()


class TestEventHandlerStreamNames:
    """事件处理器流名称测试"""

    def test_module_assigned_handler_stream(self):
        """模块分配处理器流名称正确"""
        assert ModuleAssignedHandler.stream == EventStream.MODULE_ASSIGNED

    def test_module_unassigned_handler_stream(self):
        """模块取消分配处理器流名称正确"""
        assert ModuleUnassignedHandler.stream == EventStream.MODULE_UNASSIGNED

    def test_module_menu_created_handler_stream(self):
        """模块菜单创建处理器流名称正确"""
        assert ModuleMenuCreatedHandler.stream == EventStream.MODULE_MENU_CREATED

    def test_module_menu_updated_handler_stream(self):
        """模块菜单更新处理器流名称正确"""
        assert ModuleMenuUpdatedHandler.stream == EventStream.MODULE_MENU_UPDATED

    def test_module_menu_deleted_handler_stream(self):
        """模块菜单删除处理器流名称正确"""
        assert ModuleMenuDeletedHandler.stream == EventStream.MODULE_MENU_DELETED

    def test_module_permission_created_handler_stream(self):
        """模块权限创建处理器流名称正确"""
        assert ModulePermissionCreatedHandler.stream == EventStream.MODULE_PERMISSION_CREATED

    def test_module_permission_updated_handler_stream(self):
        """模块权限更新处理器流名称正确"""
        assert ModulePermissionUpdatedHandler.stream == EventStream.MODULE_PERMISSION_UPDATED

    def test_module_permission_deleted_handler_stream(self):
        """模块权限删除处理器流名称正确"""
        assert ModulePermissionDeletedHandler.stream == EventStream.MODULE_PERMISSION_DELETED

    def test_module_role_created_handler_stream(self):
        """模块角色创建处理器流名称正确"""
        assert ModuleRoleCreatedHandler.stream == EventStream.MODULE_ROLE_CREATED

    def test_module_role_updated_handler_stream(self):
        """模块角色更新处理器流名称正确"""
        assert ModuleRoleUpdatedHandler.stream == EventStream.MODULE_ROLE_UPDATED

    def test_module_role_deleted_handler_stream(self):
        """模块角色删除处理器流名称正确"""
        assert ModuleRoleDeletedHandler.stream == EventStream.MODULE_ROLE_DELETED

    def test_module_role_permission_changed_handler_stream(self):
        """模块角色权限变更处理器流名称正确"""
        assert ModuleRolePermissionChangedHandler.stream == EventStream.MODULE_ROLE_PERMISSION_CHANGED
