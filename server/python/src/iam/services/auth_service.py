"""
用户认证服务

提供登录、登出、Token 刷新等认证功能。
"""

from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import User, UserStatus, UserTenant
from iam.schemas.login import LoginResponse
from iam.schemas.token import TokenRefreshResponse
from framework.cache.redis_util import RedisUtil
from framework.utils.crypto import hash_password, verify_password
from framework.utils.jwt import (
    decode_token,
    generate_access_token,
    generate_refresh_token,
    verify_token,
)
from framework.utils.session import (
    add_to_blacklist,
    create_session,
    delete_session,
    get_session,
    is_blacklisted,
)

_logger = logger.bind(name=__name__)

# 登录限流配置
LOGIN_RATE_LIMIT_PREFIX = "login_rate:"
LOGIN_RATE_LIMIT_WINDOW = 60  # 60 秒
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 5


def _is_redis_available() -> bool:
    """检查 Redis 是否可用"""
    return RedisUtil._client is not None


def _get_settings():
    """获取设置对象"""
    from framework.configs import get_settings

    return get_settings()


class AuthService:
    """用户认证服务"""

    @staticmethod
    async def login(session: AsyncSession, account: str, password: str, ip: str | None = None) -> LoginResponse:
        """
        用户登录

        Args:
            session: 数据库会话
            account: 账号（用户名/邮箱/手机号）
            password: 密码
            ip: 客户端 IP

        Returns:
            LoginResponse

        Raises:
            ValueError: 登录失败
        """
        # 检查登录限流（仅当 Redis 可用时）
        if ip and _is_redis_available():
            rate_key = f"{LOGIN_RATE_LIMIT_PREFIX}{ip}"
            attempts = await RedisUtil.get(rate_key)
            if attempts and int(attempts) >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
                raise ValueError("登录次数过多，请稍后再试")

        # 查询用户
        stmt = select(User).where(
            or_(
                User.username == account,
                User.email == account,
                User.phone == account,
            )
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        # 验证用户存在性和密码
        if not user or not user.password_hash:
            # 记录失败尝试（仅当 Redis 可用时）
            if ip and _is_redis_available():
                await AuthService._record_failed_attempt(ip)
            raise ValueError("用户名或密码错误")

        # 验证密码
        if not verify_password(password, user.password_hash):
            if ip and _is_redis_available():
                await AuthService._record_failed_attempt(ip)
            raise ValueError("用户名或密码错误")

        # 检查用户状态
        if user.status == UserStatus.INACTIVE:
            raise ValueError("账号已停用")
        if user.status == UserStatus.LOCKED:
            raise ValueError("账号已锁定")

        # 获取用户默认租户
        tenant_id = None
        stmt = select(UserTenant).where(
            UserTenant.user_id == user.id,
            UserTenant.is_default == True
        )
        result = await session.execute(stmt)
        user_tenant = result.scalar_one_or_none()
        if user_tenant:
            tenant_id = user_tenant.tenant_id

        # 创建会话
        session_id = await create_session(
            user_id=user.id,
            tenant_id=tenant_id,
            ip=ip,
        )

        # 生成 Token
        payload = {
            "user_id": user.id,
            "session_id": session_id,
            "version": 1,
            "roles": [],
            "permissions": [],
        }
        if tenant_id:
            payload["tenant_id"] = tenant_id

        access_token = generate_access_token(payload, AuthService._get_jwt_secret())
        refresh_token = generate_refresh_token(
            {"user_id": user.id, "session_id": session_id},
            AuthService._get_jwt_secret(),
        )

        # 更新最后登录信息
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = ip
        await session.flush()

        # 清除登录限流记录（仅当 Redis 可用时）
        if ip and _is_redis_available():
            rate_key = f"{LOGIN_RATE_LIMIT_PREFIX}{ip}"
            await RedisUtil.delete(rate_key)

        _logger.info(f"用户登录成功: {user.username}")

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=7200,  # 2 小时
            need_complete_profile=not user.profile_completed,
            tenant_id=tenant_id,
        )

    @staticmethod
    async def logout(access_token: str) -> bool:
        """
        用户登出

        Args:
            access_token: Access Token

        Returns:
            bool: 是否成功
        """
        # 解析 Token 获取 session_id 和 jti
        payload = decode_token(access_token)
        if not payload:
            return True  # Token 无效，视为已登出

        session_id = payload.get("session_id")
        jti = payload.get("jti") or session_id  # 使用 session_id 作为 jti

        # 删除会话
        if session_id:
            await delete_session(session_id)

        # 将 Token 加入黑名单（仅当 Redis 可用时）
        if jti and _is_redis_available():
            await add_to_blacklist(jti, ttl_seconds=7200)  # 2 小时

        _logger.info(f"用户登出: session_id={session_id}")
        return True

    @staticmethod
    async def refresh_token(refresh_token: str) -> TokenRefreshResponse:
        """
        刷新 Token

        Args:
            refresh_token: Refresh Token

        Returns:
            TokenRefreshResponse

        Raises:
            ValueError: Token 无效或已过期
        """
        # 验证 Refresh Token
        payload = verify_token(refresh_token, AuthService._get_jwt_secret())
        if not payload:
            raise ValueError("登录已过期，请重新登录")

        user_id = payload.get("user_id")
        session_id = payload.get("session_id")
        tenant_id = payload.get("tenant_id")

        # 检查会话是否存在
        session_data = await get_session(session_id)
        if not session_data:
            raise ValueError("登录已过期，请重新登录")

        # 检查 Refresh Token 是否在黑名单（仅当 Redis 可用时）
        jti = payload.get("jti") or session_id
        if _is_redis_available() and await is_blacklisted(jti):
            raise ValueError("登录已过期，请重新登录")

        # 将旧的 Refresh Token 加入黑名单（仅当 Redis 可用时）
        if _is_redis_available():
            await add_to_blacklist(jti, ttl_seconds=604800)  # 7 天

        # 生成新的 Token
        new_payload = {
            "user_id": user_id,
            "session_id": session_id,
            "version": session_data.get("version", 1),
            "roles": [],
            "permissions": [],
        }
        if tenant_id:
            new_payload["tenant_id"] = tenant_id

        new_access_token = generate_access_token(new_payload, AuthService._get_jwt_secret())
        new_refresh_token = generate_refresh_token(
            {"user_id": user_id, "session_id": session_id},
            AuthService._get_jwt_secret(),
        )

        return TokenRefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=7200,
        )

    @staticmethod
    async def verify_access_token(access_token: str) -> dict | None:
        """
        验证 Access Token

        Args:
            access_token: Access Token

        Returns:
            dict | None: Token payload
        """
        # 解析 Token
        payload = decode_token(access_token)
        if not payload:
            return None

        # 检查黑名单（仅当 Redis 可用时）
        jti = payload.get("jti") or payload.get("session_id")
        if jti and _is_redis_available() and await is_blacklisted(jti):
            return None

        # 检查会话版本
        session_id = payload.get("session_id")
        version = payload.get("version", 1)

        if session_id:
            session_data = await get_session(session_id)
            if not session_data:
                return None

            # 版本不匹配，需要更新权限
            if session_data.get("version", 1) != version:
                # 返回新的 payload
                return {
                    **payload,
                    "version": session_data.get("version", 1),
                    "need_refresh": True,
                }

        return payload

    @staticmethod
    async def _record_failed_attempt(ip: str) -> None:
        """记录登录失败尝试"""
        if not _is_redis_available():
            return
        rate_key = f"{LOGIN_RATE_LIMIT_PREFIX}{ip}"
        attempts = await RedisUtil.get(rate_key)
        if attempts:
            await RedisUtil.incr(rate_key)
        else:
            await RedisUtil.set(rate_key, "1", ttl=LOGIN_RATE_LIMIT_WINDOW)

    @staticmethod
    def _get_jwt_secret() -> str:
        """获取 JWT 密钥"""
        settings = _get_settings()
        return settings.iam.jwt.secret_key


# 服务单例
auth_service = AuthService()
