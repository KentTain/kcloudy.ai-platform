"""前端输出加密工具"""

import secrets
from datetime import datetime, timedelta, UTC
from typing import Any

import jwt

from framework.configs.settings import get_settings


def generate_temp_key(data: dict[str, Any]) -> tuple[str, str]:
    """
    生成临时JWT令牌和加密数据

    Args:
        data: 要加密的数据

    Returns:
        (JWT令牌, JWT密钥)
    """
    settings = get_settings()
    expired_seconds = 300  # 默认5分钟

    if settings.encryption and settings.encryption.web_out:
        expired_seconds = settings.encryption.web_out.temp_key_ttl

    # 随机生成JWT密钥
    jwt_secret = secrets.token_urlsafe(32)

    # 准备JWT
    current_time = datetime.now(UTC)
    payload = {
        "data": data,
        "iat": current_time,  # 签发时间
        "exp": current_time + timedelta(seconds=expired_seconds),  # 过期时间
        "jti": secrets.token_urlsafe(16),  # JWT ID，防止重放攻击
    }

    # 生成JWT令牌
    jwt_token = jwt.encode(payload, jwt_secret, algorithm="HS256")

    return jwt_token, jwt_secret


def decrypt_with_temp_key(temp_key: str, jwt_secret: str) -> dict[str, Any] | None:
    """
    使用JWT令牌解密数据

    Args:
        temp_key: JWT令牌
        jwt_secret: JWT密钥

    Returns:
        解密后的数据，如果过期或解密失败则返回None
    """
    try:
        # 解码JWT令牌
        payload = jwt.decode(temp_key, jwt_secret, algorithms=["HS256"])

        # 返回数据
        return payload.get("data")

    except jwt.ExpiredSignatureError:
        # JWT已过期
        return None
    except jwt.InvalidTokenError:
        # JWT无效
        return None
    except Exception:
        # 其他异常
        return None
