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

        # 空的已存在检查结果（首次同步没有历史数据）
        empty_existing = MagicMock()
        empty_existing.scalars.return_value.all.return_value = []

        # 提供充足的 side_effect 条目（sync_module_assigned 含 8+ 次 execute 调用）
        mock_session.execute.side_effect = [
            menu_result,        # 1: ModuleMenu 查询
            perm_result,        # 2: ModulePermission 查询
            role_result,        # 3: ModuleRole 查询
            role_perm_result,   # 4: ModuleRolePermission 查询
            empty_existing,     # 5: 已存在 Menu 检查
            empty_existing,     # 6: 已存在 Permission 检查
            empty_existing,     # 7: 已存在 Role 检查
            empty_existing,     # 8: 已存在 RolePermission 检查
            empty_existing,     # 9: 额外备用
            empty_existing,     # 10: 额外备用
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


class TestModuleSyncServiceAdditional:
    """模块同步服务新增方法测试"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_role_permission_created(self):
        """同步模块角色权限关联创建事件"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        mock_rp = MagicMock()
        mock_rp.module_role_id = "role-1"
        mock_rp.module_permission_id = "perm-1"

        rp_result = MagicMock()
        rp_result.scalar_one_or_none.return_value = mock_rp

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        # 角色查询：返回 Role.id
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = "tenant-role-1"

        # 权限查询：返回 Permission.id
        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = "tenant-perm-1"

        # 幂等检查：空
        empty_result = MagicMock()
        empty_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            rp_result,      # 1: ModuleRolePermission 查询
            tm_result,      # 2: 租户列表
            role_result,    # 3: 查找 Role（by ref_id）
            perm_result,    # 4: 查找 Permission（by ref_id）
            empty_result,   # 5: 幂等检查
        ]

        with patch(
            "iam.services.module_sync_service.PermissionCheckService.invalidate_tenant_permission_cache",
            new_callable=AsyncMock,
        ) as mock_cache:
            await ModuleSyncService.sync_module_role_permission_created(
                mock_session, "mrp-1", "module-1"
            )

        assert mock_session.add.call_count >= 1
        mock_cache.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_role_permission_created_skip_duplicate(self):
        """角色权限关联创建：幂等检查跳过已存在的记录"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        mock_rp = MagicMock()
        mock_rp.module_role_id = "role-1"
        mock_rp.module_permission_id = "perm-1"

        rp_result = MagicMock()
        rp_result.scalar_one_or_none.return_value = mock_rp

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = "tenant-role-1"

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = "tenant-perm-1"

        # 幂等检查：已存在
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = MagicMock()

        mock_session.execute.side_effect = [
            rp_result,       # 1: ModuleRolePermission 查询
            tm_result,       # 2: 租户列表
            role_result,     # 3: 查找 Role
            perm_result,     # 4: 查找 Permission
            existing_result, # 5: 幂等检查命中
        ]

        with patch(
            "iam.services.module_sync_service.PermissionCheckService.invalidate_tenant_permission_cache",
            new_callable=AsyncMock,
        ) as mock_cache:
            await ModuleSyncService.sync_module_role_permission_created(
                mock_session, "mrp-1", "module-1"
            )

        # 不应调用 add，因为已存在
        assert mock_session.add.call_count == 0
        mock_cache.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_role_permission_created_missing_role(self):
        """角色权限关联创建：租户角色不存在时跳过"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        mock_rp = MagicMock()
        mock_rp.module_role_id = "role-1"
        mock_rp.module_permission_id = "perm-1"

        rp_result = MagicMock()
        rp_result.scalar_one_or_none.return_value = mock_rp

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        # 角色不存在
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            rp_result,   # 1: ModuleRolePermission 查询
            tm_result,   # 2: 租户列表
            role_result, # 3: 角色查询返回 None
        ]

        with patch(
            "iam.services.module_sync_service.PermissionCheckService.invalidate_tenant_permission_cache",
            new_callable=AsyncMock,
        ) as mock_cache:
            await ModuleSyncService.sync_module_role_permission_created(
                mock_session, "mrp-1", "module-1"
            )

        assert mock_session.add.call_count == 0
        # 即使角色不存在，缓存失效仍会触发（因为 tenant_ids 已获取）
        mock_cache.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_role_permission_created_not_found(self):
        """角色权限关联创建：关联记录不存在时跳过"""
        mock_session = AsyncMock()

        rp_result = MagicMock()
        rp_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = rp_result

        await ModuleSyncService.sync_module_role_permission_created(
            mock_session, "nonexistent", "module-1"
        )

        assert mock_session.add.call_count == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_role_permission_deleted(self):
        """同步模块角色权限关联删除事件"""
        mock_session = AsyncMock()

        # 查找 Role（by ref_id）
        role_result = MagicMock()
        role_result.all.return_value = [("role-1", "tenant-1")]

        # 查找 Permission（by ref_id + tenant_id）
        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = "tenant-perm-1"

        delete_result = MagicMock()
        delete_result.rowcount = 1

        mock_session.execute.side_effect = [
            role_result,    # 1: 查找 Role
            perm_result,    # 2: 查找 Permission
            delete_result,  # 3: 删除 RolePermission
        ]

        with patch(
            "iam.services.module_sync_service.PermissionCheckService.invalidate_tenant_permission_cache",
            new_callable=AsyncMock,
        ) as mock_cache:
            await ModuleSyncService.sync_module_role_permission_deleted(
                mock_session, "role-1", "perm-1"
            )

        assert mock_session.execute.call_count >= 3
        mock_cache.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_role_permission_deleted_no_role(self):
        """角色权限关联删除：角色不存在时跳过"""
        mock_session = AsyncMock()

        role_result = MagicMock()
        role_result.all.return_value = []
        mock_session.execute.return_value = role_result

        await ModuleSyncService.sync_module_role_permission_deleted(
            mock_session, "role-nonexistent", "perm-1"
        )

        # 只执行了角色查询，没有删除操作
        assert mock_session.execute.call_count == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_menu_permission_created(self):
        """同步模块菜单权限关联创建事件"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        mock_mmp = MagicMock()
        mock_mmp.module_menu_id = "menu-1"
        mock_mmp.module_permission_id = "perm-1"

        mmp_result = MagicMock()
        mmp_result.scalar_one_or_none.return_value = mock_mmp

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        menu_result = MagicMock()
        menu_result.scalar_one_or_none.return_value = "tenant-menu-1"

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = "tenant-perm-1"

        empty_result = MagicMock()
        empty_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            mmp_result,       # 1: ModuleMenuPermission 查询
            tm_result,        # 2: 租户列表
            menu_result,      # 3: 查找 Menu（by ref_id）
            perm_result,      # 4: 查找 Permission（by ref_id）
            empty_result,     # 5: 幂等检查
        ]

        await ModuleSyncService.sync_module_menu_permission_created(
            mock_session, "mmp-1", "module-1"
        )

        assert mock_session.add.call_count >= 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_menu_permission_created_skip_duplicate(self):
        """菜单权限关联创建：幂等检查跳过已存在的记录"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        mock_mmp = MagicMock()
        mock_mmp.module_menu_id = "menu-1"
        mock_mmp.module_permission_id = "perm-1"

        mmp_result = MagicMock()
        mmp_result.scalar_one_or_none.return_value = mock_mmp

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",)]

        menu_result = MagicMock()
        menu_result.scalar_one_or_none.return_value = "tenant-menu-1"

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = "tenant-perm-1"

        # 幂等检查命中
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = MagicMock()

        mock_session.execute.side_effect = [
            mmp_result,        # 1: ModuleMenuPermission 查询
            tm_result,         # 2: 租户列表
            menu_result,       # 3: 查找 Menu
            perm_result,       # 4: 查找 Permission
            existing_result,   # 5: 幂等检查
        ]

        await ModuleSyncService.sync_module_menu_permission_created(
            mock_session, "mmp-1", "module-1"
        )

        assert mock_session.add.call_count == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_menu_permission_created_not_found(self):
        """菜单权限关联创建：关联记录不存在时跳过"""
        mock_session = AsyncMock()

        mmp_result = MagicMock()
        mmp_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mmp_result

        await ModuleSyncService.sync_module_menu_permission_created(
            mock_session, "nonexistent", "module-1"
        )

        assert mock_session.add.call_count == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_menu_permission_deleted(self):
        """同步模块菜单权限关联删除事件"""
        mock_session = AsyncMock()

        # 查找 Menu（by ref_id）
        menu_result = MagicMock()
        menu_result.all.return_value = [("menu-1", "tenant-1")]

        # 查找 Permission（by ref_id）
        perm_result = MagicMock()
        perm_result.all.return_value = [("perm-1", "tenant-1")]

        delete_result = MagicMock()
        delete_result.rowcount = 1

        mock_session.execute.side_effect = [
            menu_result,     # 1: 查找 Menu（含 tenant_id）
            perm_result,     # 2: 查找 Permission（含 tenant_id）
            delete_result,   # 3: 删除 MenuPermission
        ]

        await ModuleSyncService.sync_module_menu_permission_deleted(
            mock_session, "menu-1", "perm-1"
        )

        assert mock_session.execute.call_count >= 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_module_menu_permission_deleted_no_menu(self):
        """菜单权限关联删除：菜单不存在时跳过"""
        mock_session = AsyncMock()

        menu_result = MagicMock()
        menu_result.all.return_value = []

        # Permission 查询也需要 mock（函数会执行两个查询）
        perm_result = MagicMock()
        perm_result.all.return_value = []

        mock_session.execute.side_effect = [
            menu_result,  # 1: 查找 Menu
            perm_result,  # 2: 查找 Permission
        ]

        await ModuleSyncService.sync_module_menu_permission_deleted(
            mock_session, "menu-nonexistent", "perm-1"
        )

        # 执行了菜单和权限查询，但没有删除操作
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_permission_cache_invalidation_on_role_permission_created(self):
        """角色权限关联创建后触发缓存失效"""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        mock_rp = MagicMock()
        mock_rp.module_role_id = "role-1"
        mock_rp.module_permission_id = "perm-1"

        rp_result = MagicMock()
        rp_result.scalar_one_or_none.return_value = mock_rp

        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",), ("tenant-2",)]

        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = "tenant-role-1"

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = "tenant-perm-1"

        empty_result = MagicMock()
        empty_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            rp_result,       # 1: ModuleRolePermission 查询
            tm_result,       # 2: 租户列表（2 个租户）
            role_result,     # 3: tenant-1 角色
            perm_result,     # 4: tenant-1 权限
            empty_result,    # 5: tenant-1 幂等检查
            role_result,     # 6: tenant-2 角色
            perm_result,     # 7: tenant-2 权限
            empty_result,    # 8: tenant-2 幂等检查
        ]

        with patch(
            "iam.services.module_sync_service.PermissionCheckService.invalidate_tenant_permission_cache",
            new_callable=AsyncMock,
        ) as mock_cache:
            await ModuleSyncService.sync_module_role_permission_created(
                mock_session, "mrp-1", "module-1"
            )

            # 每个租户触发一次缓存失效
            assert mock_cache.await_count == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_permission_cache_invalidation_on_role_permission_deleted(self):
        """角色权限关联删除后触发缓存失效"""
        mock_session = AsyncMock()

        role_result = MagicMock()
        role_result.all.return_value = [
            ("role-1", "tenant-1"),
            ("role-2", "tenant-2"),
        ]

        perm_result_1 = MagicMock()
        perm_result_1.scalar_one_or_none.return_value = "tenant-perm-1"

        perm_result_2 = MagicMock()
        perm_result_2.scalar_one_or_none.return_value = "tenant-perm-2"

        delete_result = MagicMock()
        delete_result.rowcount = 1

        mock_session.execute.side_effect = [
            role_result,      # 1: 查找 Role
            perm_result_1,    # 2: tenant-1 权限
            delete_result,    # 3: 删除 tenant-1 关联
            perm_result_2,    # 4: tenant-2 权限
            delete_result,    # 5: 删除 tenant-2 关联
        ]

        with patch(
            "iam.services.module_sync_service.PermissionCheckService.invalidate_tenant_permission_cache",
            new_callable=AsyncMock,
        ) as mock_cache:
            await ModuleSyncService.sync_module_role_permission_deleted(
                mock_session, "role-1", "perm-1"
            )

            assert mock_cache.await_count == 2


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
