"""测试 UserDetailResponse Schema 转换方法

测试 from_user() 类方法的字段映射逻辑。
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from iam.schemas.user import UserDetailResponse, UserTenantResponse


class TestUserDetailResponseFromUser:
    """测试 UserDetailResponse.from_user() 方法"""

    def test_from_user_basic_fields(self):
        """测试基础字段映射"""
        # 创建 mock User 对象
        user = MagicMock()
        user.id = "user-123"
        user.tenant_id = "tenant-456"
        user.username = "testuser"
        user.email = "test@example.com"
        user.phone = "13800138000"
        user.nickname = "测试用户"
        user.avatar = "https://example.com/avatar.png"
        user.status = "active"
        user.profile_completed = True
        user.is_email_verified = True
        user.is_phone_verified = False
        user.last_login_at = datetime(2024, 1, 1, 12, 0, 0)
        user.created_at = datetime(2023, 1, 1, 0, 0, 0)

        # 调用转换方法
        result = UserDetailResponse.from_user(
            user=user,
            role_codes=["admin", "viewer"],
            permissions=["user:read", "user:write"],
            tenants=[
                UserTenantResponse(
                    id="tenant-456",
                    name="测试租户",
                    code="test_tenant",
                    is_default=True,
                )
            ],
        )

        # 验证基础字段
        assert result.id == "user-123"
        assert result.tenant_id == "tenant-456"
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.phone == "13800138000"
        assert result.nickname == "测试用户"
        assert result.avatar == "https://example.com/avatar.png"
        assert result.status == "active"
        assert result.profile_completed is True
        assert result.is_email_verified is True
        assert result.is_phone_verified is False
        assert result.last_login_at == datetime(2024, 1, 1, 12, 0, 0)
        assert result.created_at == datetime(2023, 1, 1, 0, 0, 0)

    def test_from_user_aggregated_fields(self):
        """测试聚合字段（角色、权限、租户）"""
        user = MagicMock()
        user.id = "user-123"
        user.tenant_id = "tenant-456"
        user.username = "testuser"
        user.email = None
        user.phone = None
        user.nickname = None
        user.avatar = None
        user.status = "active"
        user.profile_completed = False
        user.is_email_verified = False
        user.is_phone_verified = False
        user.last_login_at = None
        user.created_at = datetime(2023, 1, 1, 0, 0, 0)

        tenants = [
            UserTenantResponse(
                id="tenant-1",
                name="租户1",
                code="tenant_1",
                is_default=True,
            ),
            UserTenantResponse(
                id="tenant-2",
                name="租户2",
                code="tenant_2",
                is_default=False,
            ),
        ]

        result = UserDetailResponse.from_user(
            user=user,
            role_codes=["admin", "editor", "viewer"],
            permissions=["user:read", "user:write", "user:delete"],
            tenants=tenants,
        )

        # 验证聚合字段
        assert result.roles == ["admin", "editor", "viewer"]
        assert result.permissions == ["user:read", "user:write", "user:delete"]
        assert len(result.tenants) == 2
        assert result.tenants[0].id == "tenant-1"
        assert result.tenants[0].is_default is True
        assert result.tenants[1].id == "tenant-2"
        assert result.tenants[1].is_default is False

    def test_from_user_empty_collections(self):
        """测试空集合场景"""
        user = MagicMock()
        user.id = "user-123"
        user.tenant_id = "tenant-456"
        user.username = "testuser"
        user.email = None
        user.phone = None
        user.nickname = None
        user.avatar = None
        user.status = "active"
        user.profile_completed = False
        user.is_email_verified = False
        user.is_phone_verified = False
        user.last_login_at = None
        user.created_at = datetime(2023, 1, 1, 0, 0, 0)

        result = UserDetailResponse.from_user(
            user=user,
            role_codes=[],
            permissions=[],
            tenants=[],
        )

        # 验证空集合
        assert result.roles == []
        assert result.permissions == []
        assert result.tenants == []

    def test_from_user_nullable_fields(self):
        """测试可空字段为 None 的场景"""
        user = MagicMock()
        user.id = "user-123"
        user.tenant_id = "tenant-456"
        user.username = "testuser"
        user.email = None
        user.phone = None
        user.nickname = None
        user.avatar = None
        user.status = "active"
        user.profile_completed = False
        user.is_email_verified = False
        user.is_phone_verified = False
        user.last_login_at = None
        user.created_at = datetime(2023, 1, 1, 0, 0, 0)

        result = UserDetailResponse.from_user(
            user=user,
            role_codes=[],
            permissions=[],
            tenants=[],
        )

        # 验证可空字段为 None
        assert result.email is None
        assert result.phone is None
        assert result.nickname is None
        assert result.avatar is None
        assert result.last_login_at is None
