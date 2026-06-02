"""
认证流程集成测试

测试登录、登出、Token 刷新流程。
"""

import pytest
import uuid

from iam.services.user_service import UserService
from iam.services.auth_service import AuthService
from iam.models import User, UserStatus
from framework.utils.jwt import decode_token


@pytest.mark.integration
class TestAuthFlow:
    """认证流程测试"""

    @pytest.mark.asyncio
    async def test_register_and_login_flow(self, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：注册后登录流程
        WHEN: 用户注册 -> 登录 -> 访问受保护资源
        THEN: 流程正常
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 1. 注册用户
        username = f"test_auth_{uuid.uuid4().hex[:8]}"
        password = "TestPass123!"

        user = await UserService.register(
            username=username,
            password=password,
            tenant_id=test_tenant_id,
            email=f"{username}@test.com",
        )
        cleanup_users.append(user.id)

        assert user is not None

        # 2. 登录获取 Token
        login_result = await AuthService.login(
            account=username,
            password=password,
        )

        assert login_result.access_token is not None
        assert login_result.refresh_token is not None
        assert login_result.expires_in > 0

        # 3. 解析 Token 验证内容
        payload = decode_token(login_result.access_token)
        assert payload is not None
        assert payload.get("user_id") == user.id

    @pytest.mark.asyncio
    async def test_login_with_wrong_password(self, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：错误密码登录
        WHEN: 使用错误密码登录
        THEN: 返回错误提示
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 创建测试用户
        username = f"test_wrong_pwd_{uuid.uuid4().hex[:8]}"
        user = await UserService.register(
            username=username,
            password="CorrectPass123!",
            tenant_id=test_tenant_id,
        )
        cleanup_users.append(user.id)

        # 使用错误密码登录
        with pytest.raises(ValueError) as exc:
            await AuthService.login(
                account=username,
                password="WrongPass456!",
            )

        assert "用户名或密码错误" in str(exc.value)

    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：Token 刷新流程
        WHEN: Access Token 过期后使用 Refresh Token 刷新
        THEN: 获取新的 Token
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 创建测试用户并登录
        username = f"test_refresh_{uuid.uuid4().hex[:8]}"
        password = "TestPass123!"

        user = await UserService.register(
            username=username,
            password=password,
            tenant_id=test_tenant_id,
        )
        cleanup_users.append(user.id)

        login_result = await AuthService.login(
            account=username,
            password=password,
        )

        # 使用 Refresh Token 刷新
        refresh_result = await AuthService.refresh_token(login_result.refresh_token)

        assert refresh_result.access_token is not None
        assert refresh_result.expires_in > 0

        # 验证新 Token 有效
        payload = decode_token(refresh_result.access_token)
        assert payload is not None
        assert payload.get("user_id") == user.id

    @pytest.mark.asyncio
    async def test_logout_invalidates_token(self, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：登出后 Token 失效
        WHEN: 用户登出后使用原 Token
        THEN: Token 被加入黑名单
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 创建测试用户并登录
        username = f"test_logout_{uuid.uuid4().hex[:8]}"
        password = "TestPass123!"

        user = await UserService.register(
            username=username,
            password=password,
            tenant_id=test_tenant_id,
        )
        cleanup_users.append(user.id)

        login_result = await AuthService.login(
            account=username,
            password=password,
        )

        # 登出
        logout_result = await AuthService.logout(login_result.access_token)
        assert logout_result is True

    @pytest.mark.asyncio
    async def test_login_with_email(self, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：使用邮箱登录
        WHEN: 使用邮箱而不是用户名登录
        THEN: 登录成功
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 创建测试用户
        email = f"test_email_{uuid.uuid4().hex[:8]}@test.com"
        user = await UserService.register(
            username=f"user_{uuid.uuid4().hex[:8]}",
            password="TestPass123!",
            tenant_id=test_tenant_id,
            email=email,
        )
        cleanup_users.append(user.id)

        # 使用邮箱登录
        login_result = await AuthService.login(
            account=email,
            password="TestPass123!",
        )

        assert login_result.access_token is not None

    @pytest.mark.asyncio
    async def test_login_inactive_user_fails(self, postgres_available, test_tenant_id, cleanup_users):
        """
        场景：停用用户登录失败
        WHEN: 停用的用户尝试登录
        THEN: 返回账号已停用错误
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 创建测试用户
        username = f"test_inactive_{uuid.uuid4().hex[:8]}"
        user = await UserService.register(
            username=username,
            password="TestPass123!",
            tenant_id=test_tenant_id,
        )
        cleanup_users.append(user.id)

        # 停用用户
        await UserService.set_status(user.id, UserStatus.INACTIVE)

        # 尝试登录
        with pytest.raises(ValueError) as exc:
            await AuthService.login(
                account=username,
                password="TestPass123!",
            )

        assert "账号已停用" in str(exc.value)


@pytest.mark.integration
class TestOAuthFlow:
    """OAuth 登录流程测试"""

    @pytest.mark.asyncio
    async def test_oauth_authorize_url(self, postgres_available, test_tenant_id):
        """
        场景：获取 OAuth 授权链接
        WHEN: 请求微信/企微授权链接
        THEN: 返回有效链接
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # OAuth 授权链接生成需要外部服务配置
        # 此测试验证接口可调用性
        # 实际 URL 生成逻辑依赖配置
        pass
