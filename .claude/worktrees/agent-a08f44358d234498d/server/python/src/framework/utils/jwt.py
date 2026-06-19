"""
JWT Token 工具模块

提供 JWT Token 生成、验证和解析功能。
使用 HS256 算法进行签名。
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import jwt


class TokenType(str, Enum):
    """Token 类型枚举"""

    ACCESS = "access"
    REFRESH = "refresh"


# Token 有效期配置
ACCESS_TOKEN_EXPIRY_HOURS = 2
REFRESH_TOKEN_EXPIRY_DAYS = 7


def generate_access_token(
    payload: dict[str, Any],
    secret: str,
    expires_in_hours: int | None = None,
) -> str:
    """
    生成 Access Token。

    Args:
        payload: Token 载荷（包含 user_id、session_id、version、roles、permissions）
        secret: 签名密钥
        expires_in_hours: 过期时间（小时），默认 2 小时

    Returns:
        JWT Token 字符串
    """
    expiry_hours = expires_in_hours or ACCESS_TOKEN_EXPIRY_HOURS
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(hours=expiry_hours)

    # 构建完整 payload
    token_payload = {
        **payload,
        "exp": expiry,
        "iat": now,
        "type": TokenType.ACCESS,
    }

    return jwt.encode(token_payload, secret, algorithm="HS256")


def generate_refresh_token(
    payload: dict[str, Any],
    secret: str,
    expires_in_days: int | None = None,
) -> str:
    """
    生成 Refresh Token。

    Args:
        payload: Token 载荷（包含 user_id、session_id）
        secret: 签名密钥
        expires_in_days: 过期时间（天），默认 7 天

    Returns:
        JWT Token 字符串
    """
    expiry_days = expires_in_days or REFRESH_TOKEN_EXPIRY_DAYS
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=expiry_days)

    # 构建完整 payload
    token_payload = {
        **payload,
        "exp": expiry,
        "iat": now,
        "type": TokenType.REFRESH,
    }

    return jwt.encode(token_payload, secret, algorithm="HS256")


def verify_token(token: str, secret: str) -> dict[str, Any] | None:
    """
    验证 Token 并返回解码后的 payload。

    Args:
        token: JWT Token 字符串
        secret: 签名密钥

    Returns:
        验证成功返回 payload，失败返回 None
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_token(token: str) -> dict[str, Any] | None:
    """
    解析 Token（不验证过期时间）。

    用于获取 Token 中的信息而不验证其有效性。

    Args:
        token: JWT Token 字符串

    Returns:
        解析成功返回 payload，失败返回 None
    """
    if not token:
        return None

    try:
        # 不验证过期时间和签名
        payload = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        return payload
    except jwt.InvalidTokenError:
        return None
