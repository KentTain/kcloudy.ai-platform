"""
租户模块分配服务单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from tenant.services.tenant_module_service import TenantModuleService
from framework.events.domain_events import ModuleAssigned, ModuleUnassigned


class TestAssignModule:
    """assign_module 方法测试"""

    @pytest.mark.asyncio
    async def test_assign_module_success(self):
        """成功分配模块"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"
        mock_module.is_active = True
        mock_module.is_need = False

        with patch("tenant.services.tenant_module_service.async_session") as mock_session, \
             patch("tenant.services.tenant_module_service.event_publisher") as mock_publisher:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            # 模块查询
            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module

            # 已分配检查返回 None
            existing_result = MagicMock()
            existing_result.scalar_one_or_none.return_value = None

            mock_ctx.execute.side_effect = [module_result, existing_result]
            mock_ctx.add = MagicMock()
            mock_ctx.commit = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            # 设置 tenant_module.id
            def set_id_side_effect(tm):
                tm.id = "tm-1"

            mock_ctx.add.side_effect = set_id_side_effect

            result = await TenantModuleService.assign_module(
                tenant_id="tenant-1",
                module_id="module-1",
                started_at=datetime.now(),
            )

        mock_ctx.add.assert_called_once()
        mock_publisher.publish.assert_called_once()
        # 验证发布的是 ModuleAssigned 事件
        call_args = mock_publisher.publish.call_args[0][0]
        assert isinstance(call_args, ModuleAssigned)
        assert call_args.tenant_id == "tenant-1"
        assert call_args.module_id == "module-1"

    @pytest.mark.asyncio
    async def test_assign_module_module_not_found(self):
        """模块不存在时抛出错误"""
        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = None
            mock_ctx.execute.return_value = module_result

            with pytest.raises(ValueError) as exc_info:
                await TenantModuleService.assign_module(
                    tenant_id="tenant-1",
                    module_id="nonexistent",
                    started_at=datetime.now(),
                )

            assert "模块不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_module_module_inactive(self):
        """模块未启用时抛出错误"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"
        mock_module.is_active = False

        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module
            mock_ctx.execute.return_value = module_result

            with pytest.raises(ValueError) as exc_info:
                await TenantModuleService.assign_module(
                    tenant_id="tenant-1",
                    module_id="module-1",
                    started_at=datetime.now(),
                )

            assert "模块未启用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_module_already_assigned(self):
        """模块已分配时抛出错误"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"
        mock_module.is_active = True

        mock_existing = MagicMock()
        mock_existing.id = "tm-1"

        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module

            existing_result = MagicMock()
            existing_result.scalar_one_or_none.return_value = mock_existing

            mock_ctx.execute.side_effect = [module_result, existing_result]

            with pytest.raises(ValueError) as exc_info:
                await TenantModuleService.assign_module(
                    tenant_id="tenant-1",
                    module_id="module-1",
                    started_at=datetime.now(),
                )

            assert "租户已分配该模块" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_required_module_with_expiration_raises_error(self):
        """必须模块不允许设置过期时间"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "iam"
        mock_module.is_active = True
        mock_module.is_need = True  # 必须模块

        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module

            existing_result = MagicMock()
            existing_result.scalar_one_or_none.return_value = None

            mock_ctx.execute.side_effect = [module_result, existing_result]

            with pytest.raises(ValueError) as exc_info:
                await TenantModuleService.assign_module(
                    tenant_id="tenant-1",
                    module_id="module-1",
                    started_at=datetime.now(),
                    expired_at=datetime.now() + timedelta(days=30),
                )

            assert "必须模块" in str(exc_info.value)
            assert "不允许设置过期时间" in str(exc_info.value)


class TestUnassignModule:
    """unassign_module 方法测试"""

    @pytest.mark.asyncio
    async def test_unassign_module_success(self):
        """成功取消分配"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"
        mock_module.is_need = False

        mock_tenant_module = MagicMock()
        mock_tenant_module.id = "tm-1"

        with patch("tenant.services.tenant_module_service.async_session") as mock_session, \
             patch("tenant.services.tenant_module_service.event_publisher") as mock_publisher, \
             patch.object(TenantModuleService, "_check_module_role_usage") as mock_check:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module

            tm_result = MagicMock()
            tm_result.scalar_one_or_none.return_value = mock_tenant_module

            mock_ctx.execute.side_effect = [module_result, tm_result]
            mock_ctx.delete = AsyncMock()
            mock_ctx.commit = AsyncMock()

            result = await TenantModuleService.unassign_module(
                tenant_id="tenant-1",
                module_id="module-1",
            )

        assert result is True
        mock_check.assert_awaited_once()
        mock_publisher.publish.assert_called_once()
        # 验证发布的是 ModuleUnassigned 事件
        call_args = mock_publisher.publish.call_args[0][0]
        assert isinstance(call_args, ModuleUnassigned)

    @pytest.mark.asyncio
    async def test_unassign_module_not_found(self):
        """模块不存在时抛出错误"""
        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = None
            mock_ctx.execute.return_value = module_result

            with pytest.raises(ValueError) as exc_info:
                await TenantModuleService.unassign_module(
                    tenant_id="tenant-1",
                    module_id="nonexistent",
                )

            assert "模块不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unassign_required_module_raises_error(self):
        """取消必须模块分配时抛出错误"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "iam"
        mock_module.is_need = True  # 必须模块

        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module
            mock_ctx.execute.return_value = module_result

            with pytest.raises(ValueError) as exc_info:
                await TenantModuleService.unassign_module(
                    tenant_id="tenant-1",
                    module_id="module-1",
                )

            assert "必须模块" in str(exc_info.value)
            assert "禁止取消分配" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unassign_module_not_assigned_returns_false(self):
        """取消未分配的模块返回 False"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"
        mock_module.is_need = False

        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module

            tm_result = MagicMock()
            tm_result.scalar_one_or_none.return_value = None

            mock_ctx.execute.side_effect = [module_result, tm_result]

            result = await TenantModuleService.unassign_module(
                tenant_id="tenant-1",
                module_id="module-1",
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_unassign_module_with_users_raises_error(self):
        """模块角色被用户使用时抛出错误"""
        mock_module = MagicMock()
        mock_module.id = "module-1"
        mock_module.code = "demo"
        mock_module.is_need = False

        mock_tenant_module = MagicMock()
        mock_tenant_module.id = "tm-1"

        with patch("tenant.services.tenant_module_service.async_session") as mock_session, \
             patch.object(TenantModuleService, "_check_module_role_usage") as mock_check:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            module_result = MagicMock()
            module_result.scalar_one_or_none.return_value = mock_module

            tm_result = MagicMock()
            tm_result.scalar_one_or_none.return_value = mock_tenant_module

            mock_ctx.execute.side_effect = [module_result, tm_result]

            # 模拟角色使用检查抛出错误
            mock_check.side_effect = ValueError(
                "模块 demo 的角色正在被使用: 管理员(3人)，请先移除相关用户的角色后再取消分配"
            )

            with pytest.raises(ValueError) as exc_info:
                await TenantModuleService.unassign_module(
                    tenant_id="tenant-1",
                    module_id="module-1",
                )

            assert "角色正在被使用" in str(exc_info.value)


class TestCheckModuleRoleUsage:
    """_check_module_role_usage 方法测试"""

    @pytest.mark.asyncio
    async def test_no_roles_defined(self):
        """模块未定义角色时跳过检查"""
        with patch("tenant.services.tenant_module_service.async_session") as mock_session, \
             patch("tenant.services.tenant_module_service.get_iam_client") as mock_get_client:

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            # 模块角色查询返回空列表
            role_result = MagicMock()
            role_result.all.return_value = []
            mock_ctx.execute.return_value = role_result

            # 不应抛出异常
            await TenantModuleService._check_module_role_usage(
                mock_ctx, "tenant-1", "module-1", "demo"
            )

        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_roles_not_in_use(self):
        """角色未被用户使用"""
        mock_iam_client = MagicMock()
        mock_iam_client.check_module_role_usage = AsyncMock(return_value=[])

        with patch("tenant.services.tenant_module_service.async_session") as mock_session, \
             patch("tenant.services.tenant_module_service.get_iam_client") as mock_get_client:

            mock_get_client.return_value = mock_iam_client

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            # 模块角色查询返回角色 ID 列表
            role_result = MagicMock()
            role_result.all.return_value = [("role-1",), ("role-2",)]
            mock_ctx.execute.return_value = role_result

            # 不应抛出异常
            await TenantModuleService._check_module_role_usage(
                mock_ctx, "tenant-1", "module-1", "demo"
            )

        mock_iam_client.check_module_role_usage.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_roles_in_use_raises_error(self):
        """角色被用户使用时抛出错误"""
        # 模拟角色使用情况
        mock_usage = MagicMock()
        mock_usage.role_name = "管理员"
        mock_usage.user_count = 5

        mock_iam_client = MagicMock()
        mock_iam_client.check_module_role_usage = AsyncMock(return_value=[mock_usage])

        with patch("tenant.services.tenant_module_service.async_session") as mock_session, \
             patch("tenant.services.tenant_module_service.get_iam_client") as mock_get_client:

            mock_get_client.return_value = mock_iam_client

            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            role_result = MagicMock()
            role_result.all.return_value = [("role-1",)]
            mock_ctx.execute.return_value = role_result

            with pytest.raises(ValueError) as exc_info:
                await TenantModuleService._check_module_role_usage(
                    mock_ctx, "tenant-1", "module-1", "demo"
                )

            assert "管理员(5人)" in str(exc_info.value)


class TestListTenantModules:
    """list_tenant_modules 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self):
        """返回分页列表"""
        mock_tm1 = MagicMock()
        mock_tm1.id = "tm-1"
        mock_tm1.module_id = "module-1"

        mock_tm2 = MagicMock()
        mock_tm2.id = "tm-2"
        mock_tm2.module_id = "module-2"

        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            count_result = MagicMock()
            count_result.scalar.return_value = 2

            list_result = MagicMock()
            list_result.scalars.return_value.all.return_value = [mock_tm1, mock_tm2]

            mock_ctx.execute.side_effect = [count_result, list_result]

            items, total = await TenantModuleService.list_tenant_modules("tenant-1")

        assert len(items) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        """返回空列表"""
        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            count_result = MagicMock()
            count_result.scalar.return_value = 0

            list_result = MagicMock()
            list_result.scalars.return_value.all.return_value = []

            mock_ctx.execute.side_effect = [count_result, list_result]

            items, total = await TenantModuleService.list_tenant_modules("tenant-1")

        assert len(items) == 0
        assert total == 0


class TestGetTenantModule:
    """get_tenant_module 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_tenant_module(self):
        """返回租户模块分配记录"""
        mock_tm = MagicMock()
        mock_tm.id = "tm-1"
        mock_tm.tenant_id = "tenant-1"
        mock_tm.module_id = "module-1"

        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_tm
            mock_ctx.execute.return_value = result

            tm = await TenantModuleService.get_tenant_module("tenant-1", "module-1")

        assert tm is mock_tm

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """分配记录不存在时返回 None"""
        with patch("tenant.services.tenant_module_service.async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_ctx

            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            mock_ctx.execute.return_value = result

            tm = await TenantModuleService.get_tenant_module("tenant-1", "nonexistent")

        assert tm is None
