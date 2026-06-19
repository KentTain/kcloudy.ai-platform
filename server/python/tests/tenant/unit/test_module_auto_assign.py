"""
模块自动分配单元测试

测试 Protocol 定义、IAM 实现、TenantService 集成。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework.tenant.protocols import (
    ModuleAutoAssigner,
    get_module_auto_assigner,
    register_module_auto_assigner,
)


class TestModuleAutoAssignerProtocol:
    """测试 Protocol 定义"""

    def test_register_and_get(self):
        """注册后可以获取到实现"""
        mock_assigner = MagicMock(spec=ModuleAutoAssigner)
        register_module_auto_assigner(mock_assigner)
        result = get_module_auto_assigner()
        assert result is mock_assigner

    def test_get_without_register_returns_none(self):
        """未注册时返回 None"""
        register_module_auto_assigner(None)
        result = get_module_auto_assigner()
        assert result is None


class TestIamModuleAutoAssigner:
    """测试 IAM 实现"""

    @pytest.mark.asyncio
    async def test_auto_assign_assigns_all_active_modules(self, session):
        """自动分配所有活跃模块"""
        from iam.services.module_auto_assigner import IamModuleAutoAssigner

        assigner = IamModuleAutoAssigner()

        # Mock active modules query
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "iam"
        mock_module.is_active = True

        mock_module2 = MagicMock()
        mock_module2.id = "module-2"
        mock_module2.code = "demo"
        mock_module2.is_active = True

        # scalars().all() returns list of modules
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_module, mock_module2]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        # Mock existing check - no existing
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        # 第一个 execute 返回模块列表，后续返回空（幂等检查）
        session.execute.side_effect = [
            mock_result,
            mock_existing_result,
            mock_existing_result,
        ]

        with patch(
            "iam.services.module_sync_service.ModuleSyncService.sync_module_assigned",
            new_callable=AsyncMock,
        ) as mock_sync:
            await assigner.auto_assign(session, "tenant-1")

            # 验证：创建了 TenantModule
            assert session.add.call_count >= 2  # 两个模块

            # 验证：调用了 sync_module_assigned
            assert mock_sync.call_count == 2

    @pytest.mark.asyncio
    async def test_auto_assign_skips_existing(self, session):
        """跳过已分配的模块"""
        from iam.services.module_auto_assigner import IamModuleAutoAssigner

        assigner = IamModuleAutoAssigner()

        # Mock one active module
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "iam"
        mock_module.is_active = True

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_module]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        # 第一个 execute 返回模块列表，第二个返回已存在的 TenantModule
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = MagicMock()  # 已存在

        session.execute.side_effect = [mock_result, mock_existing_result]

        with patch(
            "iam.services.module_sync_service.ModuleSyncService.sync_module_assigned",
            new_callable=AsyncMock,
        ) as mock_sync:
            await assigner.auto_assign(session, "tenant-1")

            # 验证：没有创建新的 TenantModule
            assert session.add.call_count == 0
            assert mock_sync.call_count == 0


class TestTenantServiceCreate:
    """测试 TenantService.create 集成"""

    @pytest.mark.asyncio
    async def test_create_calls_auto_assigner(self, session):
        """创建租户时调用模块自动分配"""
        from tenant.services.tenant_service import TenantService

        session.refresh = AsyncMock()

        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.code = "T001"

        mock_scalar = MagicMock()
        mock_scalar.one_or_none.return_value = None
        session.execute.return_value = mock_scalar

        session.add.return_value = None

        with (
            patch(
                "tenant.services.tenant_service.generate_tenant_key",
                return_value="test_key",
            ),
            patch(
                "tenant.services.tenant_service.encrypt",
                return_value="encrypted_key",
            ),
            patch(
                "framework.tenant.protocols.get_module_auto_assigner"
            ) as mock_get_assigner,
        ):
            mock_assigner = AsyncMock()
            mock_get_assigner.return_value = mock_assigner

            await TenantService.create(
                session,
                name="测试租户",
                code="T001",
            )

            # 验证：自动分配被调用（使用同一 session）
            mock_assigner.auto_assign.assert_awaited_once()
            call_args = mock_assigner.auto_assign.await_args
            assert call_args[0][0] is session  # 同一个 session

    @pytest.mark.asyncio
    async def test_create_without_assigner_still_works(self, session):
        """没有注册分配器时创建租户仍然正常工作"""
        from tenant.services.tenant_service import TenantService

        session.refresh = AsyncMock()

        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-2"
        mock_tenant.code = "T002"

        mock_scalar = MagicMock()
        mock_scalar.one_or_none.return_value = None
        session.execute.return_value = mock_scalar

        with (
            patch(
                "tenant.services.tenant_service.generate_tenant_key",
                return_value="test_key",
            ),
            patch(
                "tenant.services.tenant_service.encrypt",
                return_value="encrypted_key",
            ),
            patch(
                "framework.tenant.protocols.get_module_auto_assigner",
                return_value=None,
            ),
        ):
            tenant = await TenantService.create(
                session,
                name="测试租户",
                code="T002",
            )
            assert tenant is not None
