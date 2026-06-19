"""
用户管理流程集成测试

测试用户注册、修改、密码管理流程。
"""

import uuid

import pytest

from iam.models import UserStatus
from iam.services.auth_service import AuthService
from iam.services.user_service import UserService


@pytest.mark.integration
class TestUserFlow:
    """用户管理流程测试"""

    @pytest.mark.asyncio
    async def test_register_flow(self, session, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：用户注册
        WHEN: 提交注册信息
        THEN: 创建用户并返回
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        username = f"test_user_{uuid.uuid4().hex[:8]}"
        password = "TestPass123!"

        user = await UserService.register(
            session,
            username=username,
            password=password,
            tenant_id=test_tenant_id,
            email=f"{username}@test.com",
        )

        cleanup_users.append(user.id)

        assert user is not None
        assert user.username == username
        assert user.tenant_id == test_tenant_id
        assert user.status == UserStatus.ACTIVE
        assert user.profile_completed is True

    @pytest.mark.asyncio
    async def test_update_profile_flow(self, session, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：修改用户信息
        WHEN: 登录后修改昵称、头像
        THEN: 信息更新成功
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 创建测试用户
        username = f"test_update_{uuid.uuid4().hex[:8]}"
        user = await UserService.register(
            session,
            username=username,
            password="TestPass123!",
            tenant_id=test_tenant_id,
        )
        cleanup_users.append(user.id)

        # 更新用户信息
        updated_user = await UserService.update_profile(
            session,
            user_id=user.id,
            nickname="新昵称",
            avatar="https://example.com/avatar.png",
        )

        assert updated_user.nickname == "新昵称"
        assert updated_user.avatar == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_change_password_flow(self, session, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：修改密码
        WHEN: 验证原密码后设置新密码
        THEN: 密码更新成功
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 创建测试用户
        username = f"test_pwd_{uuid.uuid4().hex[:8]}"
        old_password = "OldPass123!"
        new_password = "NewPass456!"

        user = await UserService.register(
            session,
            username=username,
            password=old_password,
            tenant_id=test_tenant_id,
        )
        cleanup_users.append(user.id)

        # 修改密码
        result = await UserService.change_password(
            session,
            user_id=user.id,
            old_password=old_password,
            new_password=new_password,
        )

        assert result is True

        # 验证新密码可以登录
        login_result = await AuthService.login(
            session,
            account=username,
            password=new_password,
        )

        assert login_result.access_token is not None

    @pytest.mark.asyncio
    async def test_reset_password_flow(self, session, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：重置密码
        WHEN: 管理员重置用户密码
        THEN: 密码重置成功
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 创建测试用户
        username = f"test_reset_{uuid.uuid4().hex[:8]}"
        user = await UserService.register(
            session,
            username=username,
            password="OriginalPass123!",
            tenant_id=test_tenant_id,
            email=f"{username}@test.com",
        )
        cleanup_users.append(user.id)

        # 管理员重置密码
        new_password = await UserService.admin_reset_password(session, user_id=user.id)

        assert new_password is not None
        assert len(new_password) >= 8

        # 验证新密码可以登录
        login_result = await AuthService.login(
            session,
            account=username,
            password=new_password,
        )

        assert login_result.access_token is not None

    @pytest.mark.asyncio
    async def test_register_duplicate_username_fails(self, session, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：注册重复用户名
        WHEN: 同租户内注册重复用户名
        THEN: 抛出异常
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        username = f"test_dup_{uuid.uuid4().hex[:8]}"

        # 第一次注册
        user1 = await UserService.register(
            session,
            username=username,
            password="TestPass123!",
            tenant_id=test_tenant_id,
        )
        cleanup_users.append(user1.id)

        # 第二次注册相同用户名
        with pytest.raises(ValueError) as exc:
            await UserService.register(
                session,
                username=username,
                password="TestPass456!",
                tenant_id=test_tenant_id,
            )

        assert "用户名已存在" in str(exc.value)

    @pytest.mark.asyncio
    async def test_register_weak_password_fails(self, session, postgres_available, test_tenant_id):
        """
        场景：注册弱密码
        WHEN: 使用弱密码注册
        THEN: 抛出异常
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        username = f"test_weak_{uuid.uuid4().hex[:8]}"

        with pytest.raises(ValueError):
            await UserService.register(
                session,
                username=username,
                password="123",  # 弱密码
                tenant_id=test_tenant_id,
            )

    @pytest.mark.asyncio
    async def test_update_email_uniqueness(self, session, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：更新邮箱唯一性
        WHEN: 更新邮箱为其他用户已使用的邮箱
        THEN: 抛出异常
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 创建两个测试用户
        username1 = f"test_email1_{uuid.uuid4().hex[:8]}"
        username2 = f"test_email2_{uuid.uuid4().hex[:8]}"

        user1 = await UserService.register(
            session,
            username=username1,
            password="TestPass123!",
            tenant_id=test_tenant_id,
            email=f"{username1}@test.com",
        )
        cleanup_users.append(user1.id)

        user2 = await UserService.register(
            session,
            username=username2,
            password="TestPass123!",
            tenant_id=test_tenant_id,
            email=f"{username2}@test.com",
        )
        cleanup_users.append(user2.id)

        # 尝试将 user2 的邮箱更新为 user1 的邮箱
        with pytest.raises(ValueError) as exc:
            await UserService.update_profile(
                session,
                user_id=user2.id,
                email=f"{username1}@test.com",
            )

        assert "邮箱已被其他用户使用" in str(exc.value)
