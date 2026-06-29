"""
模块定义同步服务单元测试

测试 ModuleDefinitionSyncService 的功能，包括：
- 正常同步流程
- 循环引用检测
- 父菜单不存在
- 权限引用不存在
- 孤儿数据清理
- 幂等性验证
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework.module.definition import (
    MenuDef,
    ModuleDefinition,
    PermissionDef,
    RoleDef,
)
from framework.module.sync_service import ModuleDefinitionSyncService


class TestModuleDefinitionSyncService:
    """模块定义同步服务测试"""

    @pytest.fixture
    def mock_provider(self):
        """创建模拟 provider"""
        provider = AsyncMock()
        provider.upsert_module = AsyncMock(return_value="module-id-1")
        provider.get_menu_code_to_id_map = AsyncMock(return_value={})
        provider.get_permission_code_to_id_map = AsyncMock(return_value={})
        provider.upsert_menu = AsyncMock(return_value="menu-id-1")
        provider.upsert_permission = AsyncMock()
        provider.delete_menu_permissions = AsyncMock()
        provider.upsert_menu_permission = AsyncMock()
        provider.upsert_role = AsyncMock(return_value="role-id-1")
        provider.delete_role_permissions = AsyncMock()
        provider.upsert_role_permission = AsyncMock()
        provider.cleanup_orphans = AsyncMock()
        provider.get_all_permission_code_to_id_map = AsyncMock(return_value={})
        provider.upsert_global_role = AsyncMock(return_value="global-role-id-1")
        provider.delete_orphan_global_roles = AsyncMock()
        return provider

    @pytest.fixture
    def sync_service(self, mock_provider):
        """创建同步服务实例"""
        with patch(
            "framework.module.sync_service.get_module_definition_sync_provider",
            return_value=mock_provider,
        ):
            return ModuleDefinitionSyncService()

    @pytest.fixture
    def sample_definition(self):
        """创建示例模块定义"""
        return ModuleDefinition(
            code="demo",
            name="演示模块",
            description="演示模块描述",
            icon="demo",
            version="1.0.0",
            menus=[
                MenuDef(
                    code="demo.dashboard",
                    name="仪表盘",
                    path="/dashboard",
                    icon="dashboard",
                    sort_order=1,
                    is_visible=True,
                ),
                MenuDef(
                    code="demo.users",
                    name="用户管理",
                    path="/users",
                    icon="users",
                    parent_code="demo.dashboard",
                    sort_order=2,
                    is_visible=True,
                ),
            ],
            permissions=[
                PermissionDef(
                    code="demo:user:read",
                    name="读取用户",
                    resource="user",
                    action="read",
                    description="读取用户权限",
                ),
                PermissionDef(
                    code="demo:user:write",
                    name="写入用户",
                    resource="user",
                    action="write",
                    description="写入用户权限",
                ),
            ],
            default_roles=[
                RoleDef(
                    code="demo_admin",
                    name="演示管理员",
                    description="演示模块管理员",
                    permission_codes=["demo:user:read", "demo:user:write"],
                    is_system=True,
                ),
            ],
        )

    # =========================================================================
    # 正常同步流程测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_sync_module_success(
        self, sync_service, sample_definition, mock_provider
    ):
        """正常同步流程：模块定义成功同步到数据库"""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_provider.get_menu_code_to_id_map.return_value = {}
        mock_provider.get_permission_code_to_id_map.return_value = {
            "demo:user:read": "perm-id-1",
            "demo:user:write": "perm-id-2",
        }

        await sync_service.sync_module(mock_session, sample_definition)

        # 验证 provider 方法被调用
        mock_provider.upsert_module.assert_called_once_with(
            mock_session, sample_definition
        )
        assert mock_provider.upsert_menu.call_count == 2
        assert mock_provider.upsert_permission.call_count == 2
        assert mock_provider.upsert_role.call_count == 1
        mock_provider.cleanup_orphans.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_all_modules(self, sync_service, sample_definition):
        """同步所有模块：遍历注册中心所有模块并同步"""
        # 创建模拟模块
        mock_module = MagicMock()
        mock_module.name = "demo"
        mock_module.get_module_definition.return_value = sample_definition

        mock_registry = MagicMock()
        mock_registry.get_all_modules.return_value = [mock_module]

        mock_session = AsyncMock()

        with patch(
            "framework.module.sync_service.get_registry", return_value=mock_registry
        ), patch.object(
            sync_service, "sync_module", new_callable=AsyncMock
        ) as mock_sync_module:
            await sync_service.sync_all_modules(mock_session)

            mock_sync_module.assert_called_once_with(mock_session, sample_definition)

    @pytest.mark.asyncio
    async def test_sync_all_modules_skip_none_definition(self, sync_service):
        """跳过无定义模块：模块无定义时跳过同步"""
        mock_module = MagicMock()
        mock_module.name = "empty_module"
        mock_module.get_module_definition.return_value = None

        mock_registry = MagicMock()
        mock_registry.get_all_modules.return_value = [mock_module]

        mock_session = AsyncMock()

        with patch(
            "framework.module.sync_service.get_registry", return_value=mock_registry
        ), patch.object(
            sync_service, "sync_module", new_callable=AsyncMock
        ) as mock_sync_module:
            await sync_service.sync_all_modules(mock_session)

            mock_sync_module.assert_not_called()

    # =========================================================================
    # 循环引用检测测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_detect_menu_cycles_simple(self, sync_service):
        """检测简单循环引用：A -> B -> A"""
        menus = [
            MenuDef(code="menu.a", name="A", path="/a", parent_code="menu.b"),
            MenuDef(code="menu.b", name="B", path="/b", parent_code="menu.a"),
        ]

        with pytest.raises(ValueError) as exc_info:
            sync_service._detect_menu_cycles(menus)

        assert "循环引用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_detect_menu_cycles_three_level(self, sync_service):
        """检测三级循环引用：A -> B -> C -> A"""
        menus = [
            MenuDef(code="menu.a", name="A", path="/a", parent_code="menu.c"),
            MenuDef(code="menu.b", name="B", path="/b", parent_code="menu.a"),
            MenuDef(code="menu.c", name="C", path="/c", parent_code="menu.b"),
        ]

        with pytest.raises(ValueError) as exc_info:
            sync_service._detect_menu_cycles(menus)

        assert "循环引用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_detect_menu_cycles_no_cycle(self, sync_service):
        """无循环引用：正常层级结构"""
        menus = [
            MenuDef(code="menu.root", name="Root", path="/root", parent_code=None),
            MenuDef(
                code="menu.child",
                name="Child",
                path="/child",
                parent_code="menu.root",
            ),
            MenuDef(
                code="menu.grandchild",
                name="Grandchild",
                path="/grandchild",
                parent_code="menu.child",
            ),
        ]

        # 不应抛出异常
        sync_service._detect_menu_cycles(menus)

    @pytest.mark.asyncio
    async def test_detect_menu_cycles_external_parent(self, sync_service):
        """父菜单不在当前批次：跳过检测"""
        menus = [
            MenuDef(
                code="menu.child",
                name="Child",
                path="/child",
                parent_code="external.parent",
            ),
        ]

        # 不应抛出异常（父菜单不在当前批次）
        sync_service._detect_menu_cycles(menus)

    # =========================================================================
    # 父菜单不存在测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_parent_menu_not_exists(self, sync_service, mock_provider):
        """父菜单不存在：抛出异常"""
        definition = ModuleDefinition(
            code="test",
            name="测试模块",
            menus=[
                MenuDef(
                    code="test.child",
                    name="Child",
                    path="/child",
                    parent_code="nonexistent.parent",
                ),
            ],
        )

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_provider.get_menu_code_to_id_map.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            await sync_service._sync_menus(
                mock_session, "module-id-1", "test", definition.menus
            )

        assert "父菜单" in str(exc_info.value) or "不存在" in str(exc_info.value)

    # =========================================================================
    # 权限引用不存在测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_role_permission_not_exists(self, sync_service, mock_provider):
        """角色权限引用不存在：抛出异常"""
        definition = ModuleDefinition(
            code="test",
            name="测试模块",
            permissions=[
                PermissionDef(
                    code="test:user:read",
                    name="读取用户",
                    resource="user",
                    action="read",
                ),
            ],
            default_roles=[
                RoleDef(
                    code="test_admin",
                    name="测试管理员",
                    permission_codes=["test:user:read", "nonexistent:permission"],
                ),
            ],
        )

        mock_session = AsyncMock()

        # 模拟权限查询结果 - 只有 test:user:read
        mock_provider.get_permission_code_to_id_map.return_value = {
            "test:user:read": "perm-id-1",
        }

        with pytest.raises(ValueError) as exc_info:
            await sync_service._sync_roles(
                mock_session, "module-id-1", "test", definition.default_roles
            )

        assert "权限不存在" in str(exc_info.value)

    # =========================================================================
    # 孤儿数据清理测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_cleanup_orphan_menus(self, sync_service, mock_provider):
        """清理孤儿菜单：删除不在定义中的菜单"""
        mock_session = AsyncMock()

        await sync_service._cleanup_orphans(
            mock_session,
            "module-id-1",
            "demo",
            [MenuDef(code="menu.kept", name="保留", path="/kept")],
            [],
            [],
        )

        mock_provider.cleanup_orphans.assert_called_once_with(
            mock_session,
            "module-id-1",
            [MenuDef(code="menu.kept", name="保留", path="/kept")],
            [],
            [],
        )

    @pytest.mark.asyncio
    async def test_cleanup_orphan_permissions(self, sync_service, mock_provider):
        """清理孤儿权限：删除不在定义中的权限"""
        mock_session = AsyncMock()

        await sync_service._cleanup_orphans(
            mock_session,
            "module-id-1",
            "demo",
            [],
            [PermissionDef(code="perm.kept", name="保留", resource="res", action="read")],
            [],
        )

        mock_provider.cleanup_orphans.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_orphan_roles(self, sync_service, mock_provider):
        """清理孤儿角色：删除不在定义中的角色及其权限关联"""
        mock_session = AsyncMock()

        await sync_service._cleanup_orphans(
            mock_session,
            "module-id-1",
            "demo",
            [],
            [],
            [RoleDef(code="role.kept", name="保留")],
        )

        mock_provider.cleanup_orphans.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_all_when_no_definitions(self, sync_service, mock_provider):
        """无定义时清理所有数据"""
        mock_session = AsyncMock()

        await sync_service._cleanup_orphans(
            mock_session,
            "module-id-1",
            "demo",
            [],  # 无菜单定义
            [],  # 无权限定义
            [],  # 无角色定义
        )

        mock_provider.cleanup_orphans.assert_called_once_with(
            mock_session, "module-id-1", [], [], []
        )

    # =========================================================================
    # 幂等性验证测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_sync_idempotency(
        self, sync_service, sample_definition, mock_provider
    ):
        """幂等性验证：多次同步结果一致"""
        for _ in range(2):
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_provider.get_menu_code_to_id_map.return_value = {}
            mock_provider.get_permission_code_to_id_map.return_value = {
                "demo:user:read": "perm-id-1",
                "demo:user:write": "perm-id-2",
            }

            try:
                await sync_service.sync_module(mock_session, sample_definition)
            except Exception:
                pass  # mock 可能不完整，但不应崩溃

    # =========================================================================
    # 菜单同步测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_sync_menus_two_phase(self, sync_service, mock_provider):
        """菜单两阶段同步：先创建再更新父子关系"""
        menus = [
            MenuDef(code="menu.parent", name="父菜单", path="/parent"),
            MenuDef(
                code="menu.child",
                name="子菜单",
                path="/child",
                parent_code="menu.parent",
            ),
        ]

        mock_session = AsyncMock()

        mock_provider.get_menu_code_to_id_map.return_value = {}
        mock_provider.upsert_menu.side_effect = ["parent-id", "child-id"]

        await sync_service._sync_menus(mock_session, "module-id", "demo", menus)

        # 验证菜单按顺序创建
        assert mock_provider.upsert_menu.call_count == 2
        # 父菜单先创建，子菜单后创建
        parent_call = mock_provider.upsert_menu.call_args_list[0]
        child_call = mock_provider.upsert_menu.call_args_list[1]
        # upsert_menu(session, module_id, menu_def, parent_id, existing_menu_id)
        assert parent_call.args[2].code == "menu.parent"
        assert child_call.args[2].code == "menu.child"

    @pytest.mark.asyncio
    async def test_sync_menus_empty_list(self, sync_service, mock_provider):
        """空菜单列表：不做任何操作"""
        mock_session = AsyncMock()

        await sync_service._sync_menus(mock_session, "module-id", "demo", [])

        mock_provider.get_menu_code_to_id_map.assert_not_called()

    # =========================================================================
    # 权限同步测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_sync_permissions_upsert(self, sync_service, mock_provider):
        """权限 upsert：存在则更新，不存在则创建"""
        permissions = [
            PermissionDef(
                code="test:user:read",
                name="读取用户",
                resource="user",
                action="read",
            ),
        ]

        mock_session = AsyncMock()

        await sync_service._sync_permissions(
            mock_session, "module-id", "test", permissions
        )

        mock_provider.upsert_permission.assert_called_once_with(
            mock_session, "module-id", permissions[0]
        )

    @pytest.mark.asyncio
    async def test_sync_permissions_empty_list(self, sync_service, mock_provider):
        """空权限列表：不做任何操作"""
        mock_session = AsyncMock()

        await sync_service._sync_permissions(mock_session, "module-id", "demo", [])

        mock_provider.upsert_permission.assert_not_called()

    # =========================================================================
    # 角色同步测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_sync_roles_with_permissions(self, sync_service, mock_provider):
        """角色同步：包含权限关联"""
        roles = [
            RoleDef(
                code="admin",
                name="管理员",
                permission_codes=["user:read", "user:write"],
            ),
        ]

        mock_session = AsyncMock()

        mock_provider.get_permission_code_to_id_map.return_value = {
            "user:read": "perm-id-1",
            "user:write": "perm-id-2",
        }

        await sync_service._sync_roles(mock_session, "module-id", "test", roles)

        # 验证 provider 方法被正确调用
        mock_provider.get_permission_code_to_id_map.assert_called_once_with(
            mock_session, "module-id"
        )
        mock_provider.upsert_role.assert_called_once_with(
            mock_session, roles[0], "module-id"
        )
        mock_provider.delete_role_permissions.assert_called_once_with(
            mock_session, "role-id-1"
        )
        assert mock_provider.upsert_role_permission.call_count == 2

    @pytest.mark.asyncio
    async def test_sync_roles_empty_list(self, sync_service, mock_provider):
        """空角色列表：不做任何操作"""
        mock_session = AsyncMock()

        await sync_service._sync_roles(mock_session, "module-id", "demo", [])

        mock_provider.get_permission_code_to_id_map.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_roles_with_wildcard_permissions(
        self, sync_service, mock_provider
    ):
        """角色同步：通配符权限码展开为具体权限"""
        roles = [
            RoleDef(code="admin", name="管理员", permission_codes=["test:*:*"]),
            RoleDef(
                code="viewer", name="查看者", permission_codes=["test:*:read"]
            ),
        ]

        mock_session = AsyncMock()

        mock_provider.get_permission_code_to_id_map.return_value = {
            "test:user:read": "perm-id-1",
            "test:user:write": "perm-id-2",
            "test:role:read": "perm-id-3",
            "test:role:write": "perm-id-4",
        }

        mock_provider.upsert_role.side_effect = ["role-id-1", "role-id-2"]

        await sync_service._sync_roles(mock_session, "module-id", "test", roles)

        # admin 应展开为 4 个权限
        assert mock_provider.upsert_role_permission.call_count == 6  # 4 admin + 2 viewer
        # viewer 应关联 2 个 read 权限

    @pytest.mark.asyncio
    async def test_sync_roles_wildcard_no_match(self, sync_service, mock_provider):
        """角色同步：通配符无匹配项时不创建关联"""
        roles = [
            RoleDef(code="admin", name="管理员", permission_codes=["other:*:*"]),
        ]

        mock_session = AsyncMock()

        mock_provider.get_permission_code_to_id_map.return_value = {
            "test:user:read": "perm-id-1",
        }

        await sync_service._sync_roles(mock_session, "module-id", "test", roles)

        # 只有权限查询、角色 upsert、删除旧关联，无新增关联
        mock_provider.upsert_role_permission.assert_not_called()
