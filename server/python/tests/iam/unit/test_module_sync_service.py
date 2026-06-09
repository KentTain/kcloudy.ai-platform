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

        mock_menu = MagicMock()
        mock_menu.id = "menu-1"
        mock_menu.module_id = "module-1"
        mock_menu.parent_id = None
        mock_menu.code = "dashboard"
        mock_menu.name = "仪表盘"
        mock_menu.path = "/dashboard"
        mock_menu.icon = "dashboard"
        mock_menu.is_visible = True

        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        mock_perm.code = "user:read"
        mock_perm.name = "读取用户"
        mock_perm.resource = "user"
        mock_perm.action = "read"
        mock_perm.description = "读取用户权限"

        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.code = "admin"
        mock_role.name = "管理员"
        mock_role.description = "系统管理员"
        mock_role.is_system = True

        mock_role_perm = MagicMock()
        mock_role_perm.module_role_id = "role-1"
        mock_role_perm.module_permission_id = "perm-1"

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
        mock_session.add = MagicMock()

        await ModuleSyncService.sync_module_assigned(
            mock_session, "tenant-1", "module-1", "demo"
        )

        assert mock_session.add.call_count >= 3

    @pytest.mark.asyncio
    async def test_sync_module_unassigned(self):
        """同步模块取消分配事件"""
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
    async def test_sync_module_menu_created(self):
        """同步模块菜单创建事件"""
        mock_session = AsyncMock()

        mock_module = MagicMock()
        mock_module.code = "demo"

        mock_menu = MagicMock()
        mock_menu.id = "menu-1"
        mock_menu.module_id = "module-1"
        mock_menu.parent_id = None
        mock_menu.code = "dashboard"
        mock_menu.name = "仪表盘"
        mock_menu.path = "/dashboard"
        mock_menu.icon = "dashboard"
        mock_menu.is_visible = True

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        module_result = MagicMock()
        module_result.scalar_one_or_none.return_value = mock_module

        menu_result = MagicMock()
        menu_result.scalar_one_or_none.return_value = mock_menu

        mock_session.execute.side_effect = [
            module_result,
            menu_result,
            tm_result,
        ]
        mock_session.add = MagicMock()

        await ModuleSyncService.sync_module_menu_created(
            mock_session, "menu-1", "module-1"
        )

        assert mock_session.add.call_count >= 1

    @pytest.mark.asyncio
    async def test_sync_module_permission_created(self):
        """同步模块权限创建事件"""
        mock_session = AsyncMock()

        mock_perm = MagicMock()
        mock_perm.id = "perm-1"
        mock_perm.code = "user:read"
        mock_perm.name = "读取用户"
        mock_perm.resource = "user"
        mock_perm.action = "read"
        mock_perm.description = "读取用户权限"

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = mock_perm

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        mock_session.execute.side_effect = [
            perm_result,
            tm_result,
        ]
        mock_session.add = MagicMock()

        await ModuleSyncService.sync_module_permission_created(
            mock_session, "perm-1", "module-1"
        )

        assert mock_session.add.call_count >= 1

    @pytest.mark.asyncio
    async def test_sync_module_role_created(self):
        """同步模块角色创建事件"""
        mock_session = AsyncMock()

        mock_role = MagicMock()
        mock_role.id = "role-1"
        mock_role.code = "admin"
        mock_role.name = "管理员"
        mock_role.description = "系统管理员"
        mock_role.is_system = True

        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = mock_role

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        mock_session.execute.side_effect = [
            role_result,
            tm_result,
        ]
        mock_session.add = MagicMock()

        await ModuleSyncService.sync_module_role_created(
            mock_session, "role-1", "module-1"
        )

        assert mock_session.add.call_count >= 1

    @pytest.mark.asyncio
    async def test_sync_module_role_permission_changed(self):
        """同步模块角色权限变更事件"""
        mock_session = AsyncMock()

        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = MagicMock(module_id="module-1")

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        tenant_role_result = MagicMock()
        tenant_role_result.scalar_one_or_none.return_value = "tenant-role-1"

        tenant_perm_result = MagicMock()
        tenant_perm_result.all.return_value = [("tenant-perm-1",)]

        mock_session.execute.side_effect = [
            role_result,
            tm_result,
            tenant_role_result,
            tenant_perm_result,
        ]
        mock_session.add = MagicMock()

        await ModuleSyncService.sync_module_role_permission_changed(
            mock_session, "role-1", ["perm-1"]
        )

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

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module
            mock_ctx.execute.return_value = module_result
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_assigned = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_assigned.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_missing_fields(self):
        """缺少必要字段时跳过"""
        handler = ModuleAssignedHandler()

        message = {
            "data": json.dumps({
                "tenant_id": "tenant-1",
            })
        }

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

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_unassigned = AsyncMock()

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

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_menu_created = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_menu_created.assert_awaited_once()


class TestModuleMenuUpdatedHandler:
    """模块菜单更新事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块菜单更新事件"""
        handler = ModuleMenuUpdatedHandler()

        message = {
            "data": json.dumps({
                "module_menu_id": "menu-1",
                "module_id": "module-1",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_menu_updated = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_menu_updated.assert_awaited_once()


class TestModuleMenuDeletedHandler:
    """模块菜单删除事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块菜单删除事件"""
        handler = ModuleMenuDeletedHandler()

        message = {
            "data": json.dumps({
                "module_id": "module-1",
                "menu_code": "dashboard",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_menu_deleted = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_menu_deleted.assert_awaited_once()


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

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_permission_created = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_permission_created.assert_awaited_once()


class TestModulePermissionUpdatedHandler:
    """模块权限更新事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块权限更新事件"""
        handler = ModulePermissionUpdatedHandler()

        message = {
            "data": json.dumps({
                "module_permission_id": "perm-1",
                "module_id": "module-1",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_permission_updated = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_permission_updated.assert_awaited_once()


class TestModulePermissionDeletedHandler:
    """模块权限删除事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块权限删除事件"""
        handler = ModulePermissionDeletedHandler()

        message = {
            "data": json.dumps({
                "module_id": "module-1",
                "permission_code": "user:read",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_permission_deleted = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_permission_deleted.assert_awaited_once()


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

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_role_created = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_role_created.assert_awaited_once()


class TestModuleRoleUpdatedHandler:
    """模块角色更新事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块角色更新事件"""
        handler = ModuleRoleUpdatedHandler()

        message = {
            "data": json.dumps({
                "module_role_id": "role-1",
                "module_id": "module-1",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_role_updated = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_role_updated.assert_awaited_once()


class TestModuleRoleDeletedHandler:
    """模块角色删除事件处理器测试"""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """成功处理模块角色删除事件"""
        handler = ModuleRoleDeletedHandler()

        message = {
            "data": json.dumps({
                "module_id": "module-1",
                "role_code": "admin",
            })
        }

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_role_deleted = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_role_deleted.assert_awaited_once()


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

        with patch("iam.listeners.handlers.event_handler.async_session") as mock_session,              patch("iam.listeners.handlers.event_handler.module_sync_service") as mock_sync:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx
            mock_ctx.commit = AsyncMock()

            mock_sync.sync_module_role_permission_changed = AsyncMock()

            await handler.handle(message)

        mock_sync.sync_module_role_permission_changed.assert_awaited_once()


class TestEventHandlerStreamNames:
    """事件处理器 Stream 名称测试"""

    def test_module_assigned_handler_stream(self):
        """模块分配处理器 Stream 名称"""
        assert ModuleAssignedHandler.stream == EventStream.MODULE_ASSIGNED

    def test_module_unassigned_handler_stream(self):
        """模块取消分配处理器 Stream 名称"""
        assert ModuleUnassignedHandler.stream == EventStream.MODULE_UNASSIGNED

    def test_module_menu_created_handler_stream(self):
        """模块菜单创建处理器 Stream 名称"""
        assert ModuleMenuCreatedHandler.stream == EventStream.MODULE_MENU_CREATED

    def test_module_menu_updated_handler_stream(self):
        """模块菜单更新处理器 Stream 名称"""
        assert ModuleMenuUpdatedHandler.stream == EventStream.MODULE_MENU_UPDATED

    def test_module_menu_deleted_handler_stream(self):
        """模块菜单删除处理器 Stream 名称"""
        assert ModuleMenuDeletedHandler.stream == EventStream.MODULE_MENU_DELETED

    def test_module_permission_created_handler_stream(self):
        """模块权限创建处理器 Stream 名称"""
        assert ModulePermissionCreatedHandler.stream == EventStream.MODULE_PERMISSION_CREATED

    def test_module_permission_updated_handler_stream(self):
        """模块权限更新处理器 Stream 名称"""
        assert ModulePermissionUpdatedHandler.stream == EventStream.MODULE_PERMISSION_UPDATED

    def test_module_permission_deleted_handler_stream(self):
        """模块权限删除处理器 Stream 名称"""
        assert ModulePermissionDeletedHandler.stream == EventStream.MODULE_PERMISSION_DELETED

    def test_module_role_created_handler_stream(self):
        """模块角色创建处理器 Stream 名称"""
        assert ModuleRoleCreatedHandler.stream == EventStream.MODULE_ROLE_CREATED

    def test_module_role_updated_handler_stream(self):
        """模块角色更新处理器 Stream 名称"""
        assert ModuleRoleUpdatedHandler.stream == EventStream.MODULE_ROLE_UPDATED

    def test_module_role_deleted_handler_stream(self):
        """模块角色删除处理器 Stream 名称"""
        assert ModuleRoleDeletedHandler.stream == EventStream.MODULE_ROLE_DELETED

    def test_module_role_permission_changed_handler_stream(self):
        """模块角色权限变更处理器 Stream 名称"""
        assert ModuleRolePermissionChangedHandler.stream == EventStream.MODULE_ROLE_PERMISSION_CHANGED
