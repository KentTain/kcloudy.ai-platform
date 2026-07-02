"""
Tenant 租户控制器单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from tenant.controllers.admin.tenant_controller import (
    create_tenant,
    delete_tenant,
    get_tenant,
    list_tenants,
    update_tenant,
)
from tenant.models import Tenant, TenantStatus


@pytest.mark.asyncio
class TestListTenants:
    """list_tenants 控制器测试"""

    async def test_list_tenants_returns_paginated_result(self, mock_session):
        """返回分页的租户列表"""
        mock_tenant1 = MagicMock(spec=Tenant)
        mock_tenant1.id = "tenant-1"
        mock_tenant1.code = "T001"
        mock_tenant1.name = "租户1"
        mock_tenant1.status = TenantStatus.ACTIVE

        mock_tenant2 = MagicMock(spec=Tenant)
        mock_tenant2.id = "tenant-2"
        mock_tenant2.code = "T002"
        mock_tenant2.name = "租户2"
        mock_tenant2.status = TenantStatus.ACTIVE

        with patch("tenant.controllers.admin.tenant_controller.TenantService.list_tenants") as mock_list:
            mock_list.return_value = ([mock_tenant1, mock_tenant2], 2)

            from tenant.schemas.tenant import TenantPaginatedQuery
            query = TenantPaginatedQuery(page=1, page_size=10)
            result = await list_tenants(query=query, session=mock_session)

        assert result["code"] == 200
        assert result["total"] == 2
        assert len(result["data"]) == 2
        mock_list.assert_called_once()

    async def test_list_tenants_with_keyword_filter(self, mock_session):
        """带关键词过滤的租户列表"""
        with patch("tenant.controllers.admin.tenant_controller.TenantService.list_tenants") as mock_list:
            mock_list.return_value = ([], 0)

            from tenant.schemas.tenant import TenantPaginatedQuery
            query = TenantPaginatedQuery(page=1, page_size=10, keyword="测试")
            result = await list_tenants(query=query, session=mock_session)

        assert result["total"] == 0
        mock_list.assert_called_once()


@pytest.mark.asyncio
class TestCreateTenant:
    """create_tenant 控制器测试"""

    async def test_create_tenant_success(self, mock_session):
        """成功创建租户"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.code = "T001"
        mock_tenant.name = "新租户"
        mock_tenant.status = TenantStatus.ACTIVE

        with patch("tenant.controllers.admin.tenant_controller.TenantService.create") as mock_create:
            mock_create.return_value = mock_tenant

            with patch("tenant.controllers.admin.tenant_controller.TenantService.get_by_code") as mock_get_code:
                mock_get_code.return_value = None

                from tenant.schemas.tenant import TenantCreate
                data = TenantCreate(name="新租户", code="T001")
                result = await create_tenant(data=data, session=mock_session)

        assert result["code"] == 200
        mock_create.assert_called_once()

    async def test_create_tenant_with_duplicate_code_raises_error(self, mock_session):
        """租户编码重复时抛出错误"""
        mock_existing = MagicMock(spec=Tenant)

        with patch("tenant.controllers.admin.tenant_controller.TenantService.get_by_code") as mock_get_code:
            mock_get_code.return_value = mock_existing

            from tenant.schemas.tenant import TenantCreate
            data = TenantCreate(name="租户", code="T001")

            with pytest.raises(HTTPException) as exc_info:
                await create_tenant(data=data, session=mock_session)

            assert exc_info.value.status_code == 400


@pytest.mark.asyncio
class TestGetTenant:
    """get_tenant 控制器测试"""

    async def test_get_tenant_success(self, mock_session):
        """成功获取租户详情"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.code = "T001"
        mock_tenant.name = "测试租户"
        mock_tenant.status = TenantStatus.ACTIVE

        with patch("tenant.controllers.admin.tenant_controller.TenantService.get_by_id") as mock_get:
            mock_get.return_value = mock_tenant

            with patch("tenant.controllers.admin.tenant_controller.TenantService.get_resource_bindings") as mock_bindings:
                mock_bindings.return_value = MagicMock()

                result = await get_tenant(tenant_id="tenant-1", session=mock_session)

        assert result["code"] == 200
        mock_get.assert_called_once()

    async def test_get_tenant_not_found_raises_404(self, mock_session):
        """租户不存在时抛出 404"""
        with patch("tenant.controllers.admin.tenant_controller.TenantService.get_by_id") as mock_get:
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_tenant(tenant_id="nonexistent", session=mock_session)

            assert exc_info.value.status_code == 404


@pytest.mark.asyncio
class TestUpdateTenant:
    """update_tenant 控制器测试"""

    async def test_update_tenant_success(self, mock_session):
        """成功更新租户"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.name = "更新后的租户名"

        with patch("tenant.controllers.admin.tenant_controller.TenantService.update") as mock_update:
            mock_update.return_value = mock_tenant

            from tenant.schemas.tenant import TenantUpdate
            data = TenantUpdate(name="更新后的租户名")
            result = await update_tenant(tenant_id="tenant-1", data=data, session=mock_session)

        assert result["code"] == 200
        mock_update.assert_called_once()

    async def test_update_tenant_not_found(self, mock_session):
        """租户不存在时返回 None"""
        with patch("tenant.controllers.admin.tenant_controller.TenantService.update") as mock_update:
            mock_update.return_value = None

            from tenant.schemas.tenant import TenantUpdate
            data = TenantUpdate(name="新名称")

            with pytest.raises(HTTPException) as exc_info:
                await update_tenant(tenant_id="nonexistent", data=data, session=mock_session)

            assert exc_info.value.status_code == 404


@pytest.mark.asyncio
class TestDeleteTenant:
    """delete_tenant 控制器测试"""

    async def test_delete_tenant_success(self, mock_session):
        """成功删除租户"""
        with patch("tenant.controllers.admin.tenant_controller.TenantService.delete") as mock_delete:
            mock_delete.return_value = True

            result = await delete_tenant(tenant_id="tenant-1", session=mock_session)

        assert result["code"] == 200
        mock_delete.assert_called_once()

    async def test_delete_tenant_not_found(self, mock_session):
        """租户不存在时返回 False"""
        with patch("tenant.controllers.admin.tenant_controller.TenantService.delete") as mock_delete:
            mock_delete.return_value = False

            result = await delete_tenant(tenant_id="nonexistent", session=mock_session)

        assert result["code"] == 200
        mock_delete.assert_called_once()
