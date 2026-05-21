"""
OAuth 服务

提供第三方 OAuth2 登录功能。
"""

import secrets
from urllib.parse import urlencode

from loguru import logger
from sqlalchemy import select

from models.iam import OAuthConnection, OAuthProvider, User
from framework.database.core.engine import async_session
from framework.utils.crypto import hash_password

_logger = logger.bind(name=__name__)

# OAuth 状态缓存前缀
OAUTH_STATE_PREFIX = "oauth_state:"
OAUTH_STATE_TTL = 300  # 5 分钟


class OAuthService:
    """OAuth 服务"""

    # OAuth 配置（实际应从配置读取）
    OAUTH_CONFIGS = {
        OAuthProvider.WECHAT: {
            "authorize_url": "https://open.weixin.qq.com/connect/qrconnect",
            "token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
            "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
            "client_id": "",  # 从配置读取
            "client_secret": "",  # 从配置读取
            "redirect_uri": "",  # 从配置读取
            "scope": "snsapi_login",
        },
        OAuthProvider.WEWORK: {
            "authorize_url": "https://open.work.weixin.qq.com/wwopen/sso/qrConnect",
            "token_url": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
            "userinfo_url": "https://qyapi.weixin.qq.com/cgi-bin/user/get",
            "client_id": "",  # corpid
            "client_secret": "",  # corpsecret
            "redirect_uri": "",
            "agentid": "",
        },
    }

    @staticmethod
    async def get_authorize_url(provider: str, redirect_uri: str | None = None) -> dict:
        """
        获取 OAuth 授权链接

        Args:
            provider: OAuth 提供商
            redirect_uri: 回调地址

        Returns:
            dict: 包含 authorize_url 和 state
        """
        if provider not in OAuthService.OAUTH_CONFIGS:
            raise ValueError("不支持的登录方式")

        config = OAuthService.OAUTH_CONFIGS[provider]

        # 生成 state（防 CSRF）
        state = secrets.token_urlsafe(16)

        # 缓存 state
        from framework.cache.redis_util import RedisUtil
        await RedisUtil.set(
            f"{OAUTH_STATE_PREFIX}{state}",
            provider,
            ttl=OAUTH_STATE_TTL,
        )

        # 构建授权链接
        params = {
            "appid": config["client_id"],
            "redirect_uri": redirect_uri or config["redirect_uri"],
            "response_type": "code",
            "scope": config["scope"],
            "state": state,
        }

        if provider == OAuthProvider.WECHAT:
            authorize_url = f"{config['authorize_url']}?{urlencode(params)}"
        elif provider == OAuthProvider.WEWORK:
            params["agentid"] = config.get("agentid", "")
            authorize_url = f"{config['authorize_url']}?{urlencode(params)}"
        else:
            authorize_url = f"{config['authorize_url']}?{urlencode(params)}"

        return {
            "authorize_url": authorize_url,
            "state": state,
        }

    @staticmethod
    async def handle_callback(
        provider: str,
        code: str,
        state: str,
    ) -> tuple[User, bool]:
        """
        处理 OAuth 回调

        Args:
            provider: OAuth 提供商
            code: 授权码
            state: 状态参数

        Returns:
            tuple[User, bool]: 用户对象和是否为新用户

        Raises:
            ValueError: 授权失败
        """
        # 验证 state
        from framework.cache.redis_util import RedisUtil
        cached_provider = await RedisUtil.get(f"{OAUTH_STATE_PREFIX}{state}")
        if not cached_provider or cached_provider != provider:
            raise ValueError("授权状态无效")

        # 删除 state
        await RedisUtil.delete(f"{OAUTH_STATE_PREFIX}{state}")

        # 获取 access_token 和 openid
        # TODO: 实际调用 OAuth API
        openid = f"mock_openid_{code}"
        access_token = f"mock_token_{code}"
        userinfo = {
            "openid": openid,
            "nickname": "Mock User",
            "headimgurl": "",
        }

        # 查找或创建用户
        user, is_new = await OAuthService._find_or_create_user(
            provider=provider,
            openid=openid,
            userinfo=userinfo,
            access_token=access_token,
        )

        return user, is_new

    @staticmethod
    async def _find_or_create_user(
        provider: str,
        openid: str,
        userinfo: dict,
        access_token: str,
    ) -> tuple[User, bool]:
        """查找或创建 OAuth 用户"""
        async with async_session() as session:
            # 查找已存在的 OAuth 关联
            stmt = (
                select(User)
                .join(OAuthConnection, User.id == OAuthConnection.user_id)
                .where(
                    OAuthConnection.provider == provider,
                    OAuthConnection.provider_user_id == openid,
                )
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                # 更新 token
                conn_stmt = select(OAuthConnection).where(
                    OAuthConnection.user_id == user.id,
                    OAuthConnection.provider == provider,
                )
                conn_result = await session.execute(conn_stmt)
                conn = conn_result.scalar_one()
                conn.access_token = access_token
                await session.commit()
                return user, False

            # 创建新用户
            username = f"{provider}_{openid[:8]}"
            user = User(
                username=username,
                nickname=userinfo.get("nickname", ""),
                avatar=userinfo.get("headimgurl", ""),
                password_hash=None,  # OAuth 用户无密码
                profile_completed=False,
            )
            session.add(user)
            await session.flush()

            # 创建 OAuth 关联
            conn = OAuthConnection(
                user_id=user.id,
                provider=provider,
                provider_user_id=openid,
                access_token=access_token,
            )
            session.add(conn)
            await session.commit()

            _logger.info(f"创建 OAuth 用户: {username} ({provider})")
            return user, True

    @staticmethod
    async def bind_oauth(user_id: str, provider: str, code: str) -> OAuthConnection:
        """绑定 OAuth 账号"""
        # TODO: 实现绑定逻辑
        raise NotImplementedError("绑定功能待实现")

    @staticmethod
    async def get_user_oauth_connections(user_id: str) -> list[OAuthConnection]:
        """获取用户的 OAuth 关联列表"""
        async with async_session() as session:
            stmt = select(OAuthConnection).where(OAuthConnection.user_id == user_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())


# 服务单例
oauth_service = OAuthService()
