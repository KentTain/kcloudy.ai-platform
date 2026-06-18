"""
RBAC 同步流程集成测试

测试模块分配/取消分配时的角色权限同步、菜单权限同步，
以及租户创建时的角色自动创建流程。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.integration
class TestRBACSyncFlow:
    """RBAC 同步流程测试"""

    @pytest.mark.asyncio
    async def test_module_assigned_role_permission_sync(self):
        """
        场景：模块分配时角色权限同步
        WHEN: 为租户分配一个新模块
        THEN: 模块的角色和权限同步到租户实例层
        """
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        # 模拟模块菜单
        mock_menu = MagicMock()
        mock_menu.id = "module-menu-1"
        mock_menu.module_id = "module-1"
        mock_menu.parent_id = None
        mock_menu.code = "dashboard"
        mock_menu.name = "仪表盘"
        mock_menu.path = "/dashboard"
        mock_menu.icon = "dashboard"
        mock_menu.is_visible = True

        # 模拟模块权限
        mock_perm = MagicMock()
        mock_perm.id = "module-perm-1"
        mock_perm.code = "dashboard:read"
        mock_perm.name = "读取仪表盘"
        mock_perm.resource = "dashboard"
        mock_perm.action = "read"
        mock_perm.description = "读取仪表盘数据"

        # 模拟模块角色
        mock_role = MagicMock()
        mock_role.id = "module-role-1"
        mock_role.code = "viewer"
        mock_role.name = "查看者"
        mock_role.description = "仅查看权限"
        mock_role.is_system = True

        # 模拟角色权限关联
        mock_role_perm = MagicMock()
        mock_role_perm.module_role_id = "module-role-1"
        mock_role_perm.module_permission_id = "module-perm-1"

        # 模拟菜单权限关联
        mock_menu_perm = MagicMock()
        mock_menu_perm.module_menu_id = "module-menu-1"
        mock_menu_perm.module_permission_id = "module-perm-1"

        # 查询结果
        menu_result = MagicMock()
        menu_result.scalars.return_value.all.return_value = [mock_menu]

        perm_result = MagicMock()
        perm_result.scalars.return_value.all.return_value = [mock_perm]

        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = [mock_role]

        role_perm_result = MagicMock()
        role_perm_result.scalars.return_value.all.return_value = [mock_role_perm]

        menu_perm_result = MagicMock()
        menu_perm_result.scalars.return_value.all.return_value = [mock_menu_perm]

        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []

        from iam.services.module_sync_service import ModuleSyncService

        with patch(
            "iam.services.module_sync_service.PermissionCheckService.invalidate_tenant_permission_cache",
            new_callable=AsyncMock,
        ):
            mock_session.execute.side_effect = [
                menu_result,        # 1: ModuleMenu 查询
                perm_result,        # 2: ModulePermission 查询
                role_result,        # 3: ModuleRole 查询
                role_perm_result,   # 4: ModuleRolePermission 查询
                menu_perm_result,   # 5: ModuleMenuPermission 查询
                empty_result,       # 6: 已存在 Menu 检查
                empty_result,       # 7: 已存在 Permission 检查
                empty_result,       # 8: 已存在 Role 检查
                empty_result,       # 9: 已存在 RolePermission 检查
            ]

            await ModuleSyncService.sync_module_assigned(
                mock_session, "tenant-1", "module-1", "demo"
            )

            # 验证：至少创建了 menu、permission、role
            assert mock_session.add.call_count >= 3

    @pytest.mark.asyncio
    async def test_module_assigned_menu_permission_sync(self):
        """
        场景：模块分配时菜单权限同步
        WHEN: 为租户分配一个新模块
        THEN: 模块的菜单权限关联同步到租户实例层
        """
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        # 模拟模块菜单
        mock_menu = MagicMock()
        mock_menu.id = "module-menu-1"
        mock_menu.module_id = "module-1"
        mock_menu.parent_id = None
        mock_menu.code = "dashboard"
        mock_menu.name = "仪表盘"
        mock_menu.path = "/dashboard"
        mock_menu.icon = "dashboard"
        mock_menu.is_visible = True

        # 模拟模块权限
        mock_perm = MagicMock()
        mock_perm.id = "module-perm-1"
        mock_perm.code = "dashboard:read"
        mock_perm.name = "读取仪表盘"
        mock_perm.resource = "dashboard"
        mock_perm.action = "read"
        mock_perm.description = "读取仪表盘数据"

        # 模拟模块角色
        mock_role = MagicMock()
        mock_role.id = "module-role-1"
        mock_role.code = "viewer"
        mock_role.name = "查看者"
        mock_role.description = "仅查看权限"
        mock_role.is_system = True

        # 模拟菜单权限关联（在分配同步中使用的数据）
        mock_menu_perm = MagicMock()
        mock_menu_perm.module_menu_id = "module-menu-1"
        mock_menu_perm.module_permission_id = "module-perm-1"

        from iam.services.module_sync_service import ModuleSyncService

        # 先模拟分配同步的查询
        menu_result = MagicMock()
        menu_result.scalars.return_value.all.return_value = [mock_menu]

        perm_result = MagicMock()
        perm_result.scalars.return_value.all.return_value = [mock_perm]

        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = [mock_role]

        role_perm_result = MagicMock()
        role_perm_result.scalars.return_value.all.return_value = []

        menu_perm_result = MagicMock()
        menu_perm_result.scalars.return_value.all.return_value = [mock_menu_perm]

        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []

        with patch(
            "iam.services.module_sync_service.PermissionCheckService.invalidate_tenant_permission_cache",
            new_callable=AsyncMock,
        ):
            mock_session.execute.side_effect = [
                menu_result,        # 1: ModuleMenu 查询
                perm_result,        # 2: ModulePermission 查询
                role_result,        # 3: ModuleRole 查询
                role_perm_result,   # 4: ModuleRolePermission 查询
                menu_perm_result,   # 5: ModuleMenuPermission 查询
                empty_result,       # 6: 已存在 Menu 检查
                empty_result,       # 7: 已存在 Permission 检查
                empty_result,       # 8: 已存在 Role 检查
                empty_result,       # 9: 已存在 RolePermission 检查
            ]

            await ModuleSyncService.sync_module_assigned(
                mock_session, "tenant-1", "module-1", "demo"
            )

            # 验证：至少创建了 menu、permission、role
            assert mock_session.add.call_count >= 3

    @pytest.mark.asyncio
    async def test_module_unassigned_full_cleanup(self):
        """
        场景：模块取消分配时完全清理
        WHEN: 租户取消模块分配
        THEN: 所有关联的角色、权限、菜单被删除
        """
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        # 模块角色
        role_result = MagicMock()
        role_result.all.return_value = [("module-role-1",)]

        # 模块权限
        perm_result = MagicMock()
        perm_result.all.return_value = [("module-perm-1",)]

        # 模块菜单
        menu_result = MagicMock()
        menu_result.all.return_value = [("module-menu-1",)]

        # 租户角色
        tenant_role_result = MagicMock()
        tenant_role_result.all.return_value = [("tenant-role-1",)]

        # 租户权限
        tenant_perm_result = MagicMock()
        tenant_perm_result.all.return_value = [("tenant-perm-1",)]

        # 租户菜单
        tenant_menu_result = MagicMock()
        tenant_menu_result.all.return_value = [("tenant-menu-1",)]

        delete_result = MagicMock()

        child_result = MagicMock()
        child_result.all.return_value = []

        from iam.services.module_sync_service import ModuleSyncService

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

        # 验证执行了多次查询和删除
        assert mock_session.execute.call_count == 11

    @pytest.mark.asyncio
    async def test_sync_multiple_tenants_role_permission_created(self):
        """
        场景：多租户下角色权限同步
        WHEN: 模块角色权限创建，多个租户已分配该模块
        THEN: 所有租户都获得对应的 RolePermission
        """
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        mock_rp = MagicMock()
        mock_rp.module_role_id = "role-1"
        mock_rp.module_permission_id = "perm-1"

        rp_result = MagicMock()
        rp_result.scalar_one_or_none.return_value = mock_rp

        # 3 个租户
        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",), ("tenant-2",), ("tenant-3",)]

        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = "tenant-role-1"

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = "tenant-perm-1"

        empty_result = MagicMock()
        empty_result.scalar_one_or_none.return_value = None

        from iam.services.module_sync_service import ModuleSyncService

        with patch(
            "iam.services.module_sync_service.PermissionCheckService.invalidate_tenant_permission_cache",
            new_callable=AsyncMock,
        ) as mock_cache:
            mock_session.execute.side_effect = [
                rp_result,       # 1: ModuleRolePermission 查询
                tm_result,       # 2: 租户列表
                role_result,     # 3: tenant-1
                perm_result,     # 4: tenant-1
                empty_result,    # 5: tenant-1 幂等
                role_result,     # 6: tenant-2
                perm_result,     # 7: tenant-2
                empty_result,    # 8: tenant-2 幂等
                role_result,     # 9: tenant-3
                perm_result,     # 10: tenant-3
                empty_result,    # 11: tenant-3 幂等
            ]

            await ModuleSyncService.sync_module_role_permission_created(
                mock_session, "mrp-1", "module-1"
            )

            # 3 个租户各创建 1 个 RolePermission
            assert mock_session.add.call_count == 3
            assert mock_cache.await_count == 3

    @pytest.mark.asyncio
    async def test_sync_multiple_tenants_menu_permission_created(self):
        """
        场景：多租户下菜单权限同步
        WHEN: 模块菜单权限创建，多个租户已分配该模块
        THEN: 所有租户都获得对应的 MenuPermission
        """
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        mock_mmp = MagicMock()
        mock_mmp.module_menu_id = "menu-1"
        mock_mmp.module_permission_id = "perm-1"

        mmp_result = MagicMock()
        mmp_result.scalar_one_or_none.return_value = mock_mmp

        # 2 个租户
        tm_result = MagicMock()
        tm_result.all.return_value = [("tenant-1",), ("tenant-2",)]

        menu_result = MagicMock()
        menu_result.scalar_one_or_none.return_value = "tenant-menu-1"

        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = "tenant-perm-1"

        empty_result = MagicMock()
        empty_result.scalar_one_or_none.return_value = None

        from iam.services.module_sync_service import ModuleSyncService

        mock_session.execute.side_effect = [
            mmp_result,     # 1: ModuleMenuPermission 查询
            tm_result,      # 2: 租户列表
            menu_result,    # 3: tenant-1 菜单
            perm_result,    # 4: tenant-1 权限
            empty_result,   # 5: tenant-1 幂等
            menu_result,    # 6: tenant-2 菜单
            perm_result,    # 7: tenant-2 权限
            empty_result,   # 8: tenant-2 幂等
        ]

        await ModuleSyncService.sync_module_menu_permission_created(
            mock_session, "mmp-1", "module-1"
        )

        # 2 个租户各创建 1 个 MenuPermission
        assert mock_session.add.call_count == 2


@pytest.mark.integration
class TestTenantCreationFlow:
    """租户创建流程测试"""

    @pytest.mark.asyncio
    async def test_tenant_created_roles_auto_creation(self):
        """
        场景：租户创建时角色自动创建
        WHEN: 新租户创建完成
        THEN: owner/admin/member 三个角色被自动创建
        """
        from iam.services.tenant_role_creator import IAMTenantRoleCreator

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        # 所有幂等检查返回空（角色不存在）
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            existing_result,  # owner
            existing_result,  # admin
            existing_result,  # member
            perms_result,     # 权限
        ]

        creator = IAMTenantRoleCreator()
        await creator.create_roles(mock_session, "new-tenant-1")

        # 验证：3 个角色
        assert mock_session.add.call_count == 3

    @pytest.mark.asyncio
    async def test_tenant_created_owner_permission_assignment(self):
        """
        场景：租户创建时 owner 权限分配
        WHEN: 新租户创建完成且已有同步的权限
        THEN: owner 角色获得所有已同步的权限
        """
        from iam.services.tenant_role_creator import IAMTenantRoleCreator

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        # 模拟已同步的权限
        mock_perm1 = MagicMock()
        mock_perm1.id = "perm-1"
        mock_perm2 = MagicMock()
        mock_perm2.id = "perm-2"
        mock_perm3 = MagicMock()
        mock_perm3.id = "perm-3"

        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = [
            mock_perm1, mock_perm2, mock_perm3
        ]

        rp_result = MagicMock()
        rp_result.scalar_one_or_none.return_value = None

        ur_result = MagicMock()
        ur_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            existing_result,  # owner
            existing_result,  # admin
            existing_result,  # member
            perms_result,     # 权限列表（3 个）
            rp_result,        # permis-1
            rp_result,        # permis-2
            rp_result,        # permis-3
            ur_result,        # UserRole
        ]

        creator = IAMTenantRoleCreator()
        await creator.create_roles(mock_session, "new-tenant-2", creator_user_id="user-1")

        # 3 roles + 3 RolePermissions + 1 UserRole
        assert mock_session.add.call_count == 7

    @pytest.mark.asyncio
    async def test_tenant_created_without_modules(self):
        """
        场景：租户创建时无已分配模块
        WHEN: 新租户创建但尚无模块分配
        THEN: 角色被创建，但不分配权限（因为无权限数据）
        """
        from iam.services.tenant_role_creator import IAMTenantRoleCreator

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        # 无权限
        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            existing_result,  # owner
            existing_result,  # admin
            existing_result,  # member
            perms_result,     # 无权限
        ]

        creator = IAMTenantRoleCreator()
        await creator.create_roles(mock_session, "new-tenant-3")

        # 只有 3 个角色，没有 RolePermission 和 UserRole
        assert mock_session.add.call_count == 3

    @pytest.mark.asyncio
    async def test_tenant_created_roles_duplicate_call(self):
        """
        场景：租户角色创建的幂等性
        WHEN: 重复调用角色创建方法
        THEN: 第二次调用不会重复创建角色
        """
        from iam.services.tenant_role_creator import IAMTenantRoleCreator

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        perms_result = MagicMock()
        perms_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            existing_result,  # owner
            existing_result,  # admin
            existing_result,  # member
            perms_result,
        ]

        creator = IAMTenantRoleCreator()
        await creator.create_roles(mock_session, "tenant-1")

        first_call_count = mock_session.add.call_count

        # 重置模拟：第二次调用，角色已存在
        mock_session.add = MagicMock()
        mock_session.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=MagicMock())),  # owner 已存在
            MagicMock(scalar_one_or_none=MagicMock(return_value=MagicMock())),  # admin 已存在
            MagicMock(scalar_one_or_none=MagicMock(return_value=MagicMock())),  # member 已存在
            perms_result,
        ]

        await creator.create_roles(mock_session, "tenant-1")

        # 第二次调用不应创建任何角色
        assert mock_session.add.call_count == 0
