"""测试 UserService 聚合方法

测试 get_user_detail() 聚合方法的并行查询和数据组装逻辑。
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from iam.schemas.user import UserDetailResponse, UserTenantResponse


class TestGetUserDetail:
    """测试 UserService.get_user_detail() 聚合方法"""

    @pytest.mark.asyncio
    async def test_get_user_detail_success(self, session):
        """测试成功获取用户详情"""
        # 创建 mock User 对象
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.tenant_id = "tenant-456"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.phone = "13800138000"
        mock_user.nickname = "测试用户"
        mock_user.avatar = None
        mock_user.status = "active"
        mock_user.profile_completed = True
        mock_user.is_email_verified = True
        mock_user.is_phone_verified = False
        mock_user.last_login_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_user.created_at = datetime(2023, 1, 1, 0, 0, 0)

        # 创建 mock Role 对象
        mock_role = MagicMock()
        mock_role.code = "admin"

        # 准备测试数据
        mock_permissions = ["user:read", "user:write"]
        mock_tenants = [
            UserTenantResponse(
                id="tenant-456",
                name="测试租户",
                code="test_tenant",
                is_default=True,
            )
        ]

        # 使用 patch 模拟各个依赖调用
        with patch(
            "iam.services.user_service.UserService.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_user,
        ), patch(
            "iam.services.role_service.user_role_service.get_user_roles",
            new_callable=AsyncMock,
            return_value=[mock_role],
        ), patch(
            "iam.services.permission_service.permission_check_service.get_user_permissions",
            new_callable=AsyncMock,
            return_value=mock_permissions,
        ), patch(
            "iam.services.user_service.UserService._get_user_tenants_with_detail",
            new_callable=AsyncMock,
            return_value=mock_tenants,
        ), patch(
            "iam.services.user_menu_service.user_menu_service.get_user_menus",
            new_callable=AsyncMock,
            return_value=[],
        ):
            from iam.services.user_service import user_service

            result = await user_service.get_user_detail(session, "user-123")

            # 验证返回结果
            assert result is not None
            assert isinstance(result, UserDetailResponse)
            assert result.id == "user-123"
            assert result.username == "testuser"
            assert result.roles == ["admin"]
            assert result.permissions == ["user:read", "user:write"]
            assert len(result.tenants) == 1
            assert result.tenants[0].id == "tenant-456"

    @pytest.mark.asyncio
    async def test_get_user_detail_user_not_found(self, session):
        """测试用户不存在时返回 None"""
        with patch(
            "iam.services.user_service.UserService.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            from iam.services.user_service import user_service

            result = await user_service.get_user_detail(session, "nonexistent-user")

            # 验证返回 None
            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_detail_empty_data(self, session):
        """测试用户无角色、权限、租户的场景"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.tenant_id = "tenant-456"
        mock_user.username = "testuser"
        mock_user.email = None
        mock_user.phone = None
        mock_user.nickname = None
        mock_user.avatar = None
        mock_user.status = "active"
        mock_user.profile_completed = False
        mock_user.is_email_verified = False
        mock_user.is_phone_verified = False
        mock_user.last_login_at = None
        mock_user.created_at = datetime(2023, 1, 1, 0, 0, 0)

        with patch(
            "iam.services.user_service.UserService.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_user,
        ), patch(
            "iam.services.role_service.user_role_service.get_user_roles",
            new_callable=AsyncMock,
            return_value=[],  # 无角色
        ), patch(
            "iam.services.permission_service.permission_check_service.get_user_permissions",
            new_callable=AsyncMock,
            return_value=[],  # 无权限
        ), patch(
            "iam.services.user_service.UserService._get_user_tenants_with_detail",
            new_callable=AsyncMock,
            return_value=[],  # 无租户
        ), patch(
            "iam.services.user_menu_service.user_menu_service.get_user_menus",
            new_callable=AsyncMock,
            return_value=[],
        ):
            from iam.services.user_service import user_service

            result = await user_service.get_user_detail(session, "user-123")

            # 验证返回结果为空集合
            assert result is not None
            assert result.roles == []
            assert result.permissions == []
            assert result.tenants == []


class TestGetUserTenantsWithDetail:
    """测试 UserService._get_user_tenants_with_detail() 内部方法"""

    @pytest.mark.asyncio
    async def test_get_tenants_with_detail_success(self, session):
        """测试成功获取租户详情"""
        # Mock UserTenant 数据
        mock_user_tenants = [
            {"tenant_id": "tenant-1", "role": "owner", "is_default": True},
            {"tenant_id": "tenant-2", "role": "member", "is_default": False},
        ]

        # Mock Tenant 数据
        mock_tenant_1 = MagicMock()
        mock_tenant_1.id = "tenant-1"
        mock_tenant_1.name = "租户1"
        mock_tenant_1.code = "tenant_1"

        mock_tenant_2 = MagicMock()
        mock_tenant_2.id = "tenant-2"
        mock_tenant_2.name = "租户2"
        mock_tenant_2.code = "tenant_2"

        mock_tenants_info = {
            "tenant-1": mock_tenant_1,
            "tenant-2": mock_tenant_2,
        }

        with patch(
            "iam.services.user_service.UserService.get_user_tenants_detail",
            new_callable=AsyncMock,
            return_value=mock_user_tenants,
        ), patch(
            "tenant.services.tenant_service.tenant_service.get_tenants_by_ids",
            new_callable=AsyncMock,
            return_value=mock_tenants_info,
        ):
            from iam.services.user_service import user_service

            result = await user_service._get_user_tenants_with_detail(session, "user-123")

            # 验证返回结果
            assert len(result) == 2
            assert result[0].id == "tenant-1"
            assert result[0].name == "租户1"
            assert result[0].is_default is True
            assert result[1].id == "tenant-2"
            assert result[1].is_default is False

    @pytest.mark.asyncio
    async def test_get_tenants_with_detail_empty(self, session):
        """测试用户无租户的场景"""
        with patch(
            "iam.services.user_service.UserService.get_user_tenants_detail",
            new_callable=AsyncMock,
            return_value=[],
        ):
            from iam.services.user_service import user_service

            result = await user_service._get_user_tenants_with_detail(session, "user-123")

            # 验证返回空列表
            assert result == []
