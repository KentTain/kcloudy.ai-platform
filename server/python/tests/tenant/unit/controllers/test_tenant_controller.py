"""
Tenant 租户控制器单元测试

测试控制器的参数校验和错误处理逻辑。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
class TestCreateTenant:
    """create_tenant 控制器测试"""

    async def test_create_tenant_with_duplicate_code_raises_error(self, mock_session):
        """租户编码重复时抛出 400 错误"""
        from tenant.controllers.admin.tenant_controller import create_tenant
        from tenant.schemas.admin.tenant import TenantCreate

        mock_existing = MagicMock()

        with patch(
            "tenant.controllers.admin.tenant_controller.TenantService.get_by_code"
        ) as mock_get_code:
            mock_get_code.return_value = mock_existing

            data = TenantCreate(name="租户", code="T001")
            admin = {"user_id": "admin-1"}

            with pytest.raises(HTTPException) as exc_info:
                await create_tenant(data=data, admin=admin, session=mock_session)

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "租户编码已存在"


@pytest.mark.asyncio
class TestGetTenant:
    """get_tenant 控制器测试"""

    async def test_get_tenant_not_found_raises_404(self, mock_session):
        """租户不存在时抛出 404"""
        from tenant.controllers.admin.tenant_controller import get_tenant

        with patch(
            "tenant.controllers.admin.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = None

            admin = {"user_id": "admin-1"}

            with pytest.raises(HTTPException) as exc_info:
                await get_tenant(tenant_id="nonexistent", admin=admin, session=mock_session)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "租户不存在"
