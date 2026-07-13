"""UserResponse 角色权限字段测试"""

from iam.schemas.user import UserResponse


def test_user_vo_has_roles_and_permissions():
    """UserResponse 应包含 roles 和 permissions 字段"""
    user_vo = UserResponse(
        id="test-id",
        tenant_id="tenant-id",
        username="testuser",
        email="test@example.com",
        phone=None,
        nickname="Test User",
        avatar=None,
        status="active",
        profile_completed=True,
        is_email_verified=False,
        is_phone_verified=False,
        last_login_at=None,
        created_at="2024-01-01T00:00:00Z",
        roles=["admin", "viewer"],
        permissions=["iam:user:read", "iam:role:read"],
    )
    assert user_vo.roles == ["admin", "viewer"]
    assert user_vo.permissions == ["iam:user:read", "iam:role:read"]
