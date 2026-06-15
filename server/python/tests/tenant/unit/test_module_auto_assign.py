"""
模块自动分配单元测试

测试 Protocol 定义、IAM 实现、TenantService 集成。
"""

from datetime import datetime
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
    async def test_auto_assign_assigns_all_active_modules(self):
        """自动分配所有活跃模块"""
        from iam.services.module_auto_assigner import IamModuleAutoAssigner

        assigner = IamModuleAutoAssigner()

        # Mock session
        mock_session = AsyncMock()

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
        mock_session.execute.return_value = mock_result

        # Mock existing check - no existing
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_existing_result

        with patch(
            "iam.services.module_auto_assigner.module_sync_service"
        ) as mock_sync:
            await assigner.auto_assign(mock_session, "tenant-1")

            # 验证：查询活跃模块
            execute_calls = [call[0] for call in mock_session.execute.call_args_list]
            assert any("is_active" in str(c) for c in execute_calls)

            # 验证：创建了 TenantModule
            assert mock_session.add.call_count >= 2  # 两个模块

            # 验证：调用了 sync_module_assigned
            assert mock_sync.sync_module_assigned.call_count == 2

    @pytest.mark.asyncio
    async def test_auto_assign_skips_existing(self):
        """跳过已分配的模块"""
        from iam.services.module_auto_assigner import IamModuleAutoAssigner

        assigner = IamModuleAutoAssigner()
        mock_session = AsyncMock()

        # Mock one active module
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "iam"
        mock_module.is_active = True

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_module]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # 第一次返回模块查询，第二次返回已存在的 TenantModule
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = MagicMock()  # 已存在
        mock_session.execute.return_value = mock_existing_result

        with patch(
            "iam.services.module_auto_assigner.module_sync_service"
        ) as mock_sync:
            await assigner.auto_assign(mock_session, "tenant-1")

            # 验证：没有创建新的 TenantModule
            assert mock_session.add.call_count == 0
            assert mock_sync.sync_module_assigned.call_count == 0


class TestTenantServiceCreate:
    """测试 TenantService.create 集成"""

    @pytest.mark.asyncio
    async def test_create_calls_auto_assigner(self):
        """创建租户时调用模块自动分配"""
        from tenant.services.tenant_service import TenantService

        # Mock 数据库 session
        mock_session = AsyncMock()
        mock_session.refresh = AsyncMock()

        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.code = "T001"

        mock_scalar = MagicMock()
        mock_scalar.one_or_none.return_value = None
        mock_session.execute.return_value = mock_scalar

        # Mock 上下文管理器
        mock_cm = MagicMock()
        mock_cm.__aenter__.return_value = mock_session
        mock_session.add.return_value = None

        with (
            patch(
                "tenant.services.tenant_service.async_session",
                return_value=mock_cm,
            ),
            patch(
                "tenant.services.tenant_service.generate_tenant_key",
                return_value="test_key",
            ),
            patch(
                "tenant.services.tenant_service.encrypt",
                return_value="encrypted_key",
            ),
            patch(
                "tenant.services.tenant_service.get_module_auto_assigner"
            ) as mock_get_assigner,
        ):
            mock_assigner = AsyncMock()
            mock_get_assigner.return_value = mock_assigner

            await TenantService.create(
                name="测试租户",
                code="T001",
            )

            # 验证：自动分配被调用
            mock_assigner.auto_assign.assert_awaited_once_with(
                mock_session, mock_tenant.id
            )

    @pytest.mark.asyncio
    async def test_create_without_assigner_still_works(self):
        """没有注册分配器时创建租户仍然正常工作"""
        from tenant.services.tenant_service import TenantService

        mock_session = AsyncMock()
        mock_session.refresh = AsyncMock()

        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-2"
        mock_tenant.code = "T002"

        mock_scalar = MagicMock()
        mock_scalar.one_or_none.return_value = None
        mock_session.execute.return_value = mock_scalar

        mock_cm = MagicMock()
        mock_cm.__aenter__.return_value = mock_session

        with (
            patch(
                "tenant.services.tenant_service.async_session",
                return_value=mock_cm,
            ),
            patch(
                "tenant.services.tenant_service.generate_tenant_key",
                return_value="test_key",
            ),
            patch(
                "tenant.services.tenant_service.encrypt",
                return_value="encrypted_key",
            ),
            patch(
                "tenant.services.tenant_service.get_module_auto_assigner",
                return_value=None,
            ),
        ):
            tenant = await TenantService.create(
                name="测试租户",
                code="T002",
            )
            assert tenant is not None
