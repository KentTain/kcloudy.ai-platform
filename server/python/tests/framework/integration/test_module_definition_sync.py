"""
模块定义同步集成测试

测试 ModuleDefinitionSyncService 与真实数据库的交互。
使用 @pytest.mark.integration 标记。

测试场景：
- 端到端同步流程
- 模块定义持久化
- 菜单、权限、角色关联同步
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.integration


class TestModuleDefinitionSyncWithMock:
    """使用 Mock 的集成测试（不依赖真实数据库）"""

    @pytest.fixture
    def sync_service(self):
        """创建同步服务实例"""
        from framework.module.sync_service import ModuleDefinitionSyncService
        return ModuleDefinitionSyncService()

    @pytest.mark.asyncio
    async def test_sync_module_with_mock_session(self, sync_service):
        """
        场景：使用 Mock 会话测试同步流程

        GIVEN 模块定义和 Mock 数据库会话
        WHEN 调用 sync_module
        THEN 正确执行同步逻辑
        """
        from framework.module.definition import MenuDef, ModuleDefinition

        unique_suffix = uuid.uuid4().hex[:8]

        definition = ModuleDefinition(
            code=f"mock_test_{unique_suffix}",
            name="Mock 测试",
            menus=[
                MenuDef(
                    code=f"mock_{unique_suffix}.menu1",
                    name="菜单1",
                    path="/menu1",
                ),
            ],
        )

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        # 模拟 insert returning 结果
        module_result = MagicMock()
        module_result.scalar_one.return_value = "module-id-1"

        menu_result = MagicMock()
        menu_result.scalar_one.return_value = "menu-id-1"

        orphan_role_result = MagicMock()
        orphan_role_result.all.return_value = []

        mock_session.execute.side_effect = [
            module_result,
            menu_result,
            MagicMock(),  # cleanup menus
            MagicMock(),  # cleanup perms
            orphan_role_result,  # query orphan roles
        ]

        await sync_service.sync_module(mock_session, definition)

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_all_modules_with_registry(self, sync_service):
        """
        场景：同步注册中心所有模块

        GIVEN 注册中心有多个模块
        WHEN 调用 sync_all_modules
        THEN 所有模块都被同步
        """
        from framework.module.definition import ModuleDefinition

        unique_suffix = uuid.uuid4().hex[:8]

        definition1 = ModuleDefinition(
            code=f"module1_{unique_suffix}",
            name="模块1",
        )

        definition2 = ModuleDefinition(
            code=f"module2_{unique_suffix}",
            name="模块2",
        )

        mock_module1 = MagicMock()
        mock_module1.name = f"module1_{unique_suffix}"
        mock_module1.get_module_definition.return_value = definition1

        mock_module2 = MagicMock()
        mock_module2.name = f"module2_{unique_suffix}"
        mock_module2.get_module_definition.return_value = definition2

        mock_registry = MagicMock()
        mock_registry.get_all_modules.return_value = [mock_module1, mock_module2]

        mock_session = AsyncMock()

        with patch('framework.module.sync_service.get_registry', return_value=mock_registry), \
             patch.object(sync_service, 'sync_module', new_callable=AsyncMock) as mock_sync:

            await sync_service.sync_all_modules(mock_session)

            assert mock_sync.call_count == 2


class TestModuleRegistryIntegration:
    """模块注册中心集成测试"""

    @pytest.mark.asyncio
    async def test_registry_with_module_definition(self):
        """
        场景：注册带定义的模块

        GIVEN 模块实现了 get_module_definition 方法
        WHEN 注册到注册中心
        THEN 可以正确获取模块定义
        """
        from framework.module.definition import ModuleDefinition
        from framework.module.registry import ModuleRegistry, get_registry

        # 重置注册中心
        ModuleRegistry.reset()

        registry = get_registry()

        # 创建模拟模块
        mock_module = MagicMock()
        mock_module.name = "test_definition_module"
        mock_module.schema = "test_definition"
        mock_module.dependencies = []

        definition = ModuleDefinition(
            code="test_definition",
            name="测试定义模块",
        )
        mock_module.get_module_definition.return_value = definition
        mock_module.get_base.return_value = MagicMock()
        mock_module.get_routers.return_value = []
        mock_module.get_middlewares.return_value = []
        mock_module.get_lifespan_hooks.return_value = []
        mock_module.get_seeds.return_value = {}
        mock_module.get_task_setup.return_value = None
        mock_module.get_listener_setup.return_value = None

        registry.register(mock_module)

        assert registry.has_module("test_definition_module")

        retrieved = registry.get_module("test_definition_module")
        assert retrieved is not None
        assert retrieved.get_module_definition() == definition

        # 清理
        ModuleRegistry.reset()

    @pytest.mark.asyncio
    async def test_registry_module_without_definition(self):
        """
        场景：注册无定义的模块

        GIVEN 模块未实现 get_module_definition 方法（返回 None）
        WHEN 注册到注册中心
        THEN 可以正常注册，但定义返回 None
        """
        from framework.module.registry import ModuleRegistry, get_registry

        # 重置注册中心
        ModuleRegistry.reset()

        registry = get_registry()

        mock_module = MagicMock()
        mock_module.name = "test_no_definition_module"
        mock_module.schema = "test_no_def"
        mock_module.dependencies = []
        mock_module.get_module_definition.return_value = None
        mock_module.get_base.return_value = MagicMock()
        mock_module.get_routers.return_value = []
        mock_module.get_middlewares.return_value = []
        mock_module.get_lifespan_hooks.return_value = []
        mock_module.get_seeds.return_value = {}
        mock_module.get_task_setup.return_value = None
        mock_module.get_listener_setup.return_value = None

        registry.register(mock_module)

        retrieved = registry.get_module("test_no_definition_module")
        assert retrieved is not None
        assert retrieved.get_module_definition() is None

        # 清理
        ModuleRegistry.reset()


class TestModuleDefinitionLogic:
    """模块定义逻辑测试"""

    @pytest.mark.unit
    def test_module_definition_creation(self):
        """测试创建模块定义"""
        from framework.module.definition import (
            MenuDef,
            ModuleDefinition,
            PermissionDef,
            RoleDef,
        )

        definition = ModuleDefinition(
            code="test_module",
            name="测试模块",
            description="这是一个测试模块",
            icon="test",
            version="1.0.0",
            menus=[
                MenuDef(
                    code="test.dashboard",
                    name="仪表盘",
                    path="/dashboard",
                    icon="dashboard",
                    sort_order=1,
                ),
            ],
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
                    permission_codes=["test:user:read"],
                    is_system=True,
                ),
            ],
        )

        assert definition.code == "test_module"
        assert definition.name == "测试模块"
        assert len(definition.menus) == 1
        assert len(definition.permissions) == 1
        assert len(definition.default_roles) == 1

    @pytest.mark.unit
    def test_menu_def_defaults(self):
        """测试菜单定义默认值"""
        from framework.module.definition import MenuDef

        menu = MenuDef(
            code="test.menu",
            name="测试菜单",
            path="/test",
        )

        assert menu.icon is None
        assert menu.parent_code is None
        assert menu.sort_order == 0
        assert menu.is_visible is True

    @pytest.mark.unit
    def test_permission_def_creation(self):
        """测试权限定义创建"""
        from framework.module.definition import PermissionDef

        perm = PermissionDef(
            code="test:user:read",
            name="读取用户",
            resource="user",
            action="read",
            description="读取用户权限",
        )

        assert perm.code == "test:user:read"
        assert perm.resource == "user"
        assert perm.action == "read"

    @pytest.mark.unit
    def test_role_def_defaults(self):
        """测试角色定义默认值"""
        from framework.module.definition import RoleDef

        role = RoleDef(
            code="test_user",
            name="测试用户",
        )

        assert role.description is None
        assert role.permission_codes == []
        assert role.is_system is False
