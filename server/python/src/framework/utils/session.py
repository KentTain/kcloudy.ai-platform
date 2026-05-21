"""
会话管理工具模块

提供基于 Redis 的用户会话管理功能，包括会话创建、查询、删除和 Token 黑名单。
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from nanoid import generate

from framework.cache.redis_util import RedisUtil


# 默认会话 TTL（7 天）
DEFAULT_SESSION_TTL_DAYS = 7


def get_session_key(session_id: str, key_prefix: str = "") -> str:
    """
    生成会话存储 Key。

    Args:
        session_id: 会话 ID
        key_prefix: Key 前缀

    Returns:
        完整的会话 Key
    """
    return f"{key_prefix}session:{session_id}"


def get_blacklist_key(jti: str, key_prefix: str = "") -> str:
    """
    生成黑名单存储 Key。

    Args:
        jti: Token 的 JTI（JWT ID）
        key_prefix: Key 前缀

    Returns:
        完整的黑名单 Key
    """
    return f"{key_prefix}blacklist:{jti}"


async def create_session(
    user_id: str,
    tenant_id: str,
    device_info: str | None = None,
    ip: str | None = None,
    ttl: timedelta | None = None,
    key_prefix: str = "",
) -> str:
    """
    创建用户会话。

    Args:
        user_id: 用户 ID
        tenant_id: 租户 ID
        device_info: 设备信息
        ip: 客户端 IP
        ttl: 会话过期时间，默认 7 天
        key_prefix: Redis Key 前缀

    Returns:
        会话 ID
    """
    # 生成会话 ID
    session_id = generate(size=21)

    # 会话数据
    session_data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "version": 1,
        "device_info": device_info,
        "ip": ip,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # 计算 TTL
    ttl_seconds = int((ttl or timedelta(days=DEFAULT_SESSION_TTL_DAYS)).total_seconds())

    # 存储到 Redis
    key = get_session_key(session_id, key_prefix)
    await RedisUtil.set(key, json.dumps(session_data), ttl=ttl_seconds)

    return session_id


async def get_session(
    session_id: str,
    key_prefix: str = "",
) -> dict[str, Any] | None:
    """
    获取会话数据。

    Args:
        session_id: 会话 ID
        key_prefix: Redis Key 前缀

    Returns:
        会话数据，不存在则返回 None
    """
    key = get_session_key(session_id, key_prefix)
    data = await RedisUtil.get(key)

    if data is None:
        return None

    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


async def delete_session(session_id: str, key_prefix: str = "") -> None:
    """
    删除会话。

    Args:
        session_id: 会话 ID
        key_prefix: Redis Key 前缀
    """
    key = get_session_key(session_id, key_prefix)
    await RedisUtil.delete(key)


async def update_session_version(session_id: str, key_prefix: str = "") -> int:
    """
    更新会话版本号。

    用于权限变更时使 Token 中的版本号失效。

    Args:
        session_id: 会话 ID
        key_prefix: Redis Key 前缀

    Returns:
        更新后的版本号
    """
    session = await get_session(session_id, key_prefix)
    if session is None:
        return 0

    # 增加版本号
    session["version"] = session.get("version", 1) + 1

    # 获取剩余 TTL
    key = get_session_key(session_id, key_prefix)
    # 更新会话数据（保持原 TTL）
    await RedisUtil.set(key, json.dumps(session))

    return session["version"]


async def add_to_blacklist(
    jti: str,
    ttl_seconds: int,
    key_prefix: str = "",
) -> None:
    """
    将 Token 添加到黑名单。

    Args:
        jti: Token 的 JTI（JWT ID）
        ttl_seconds: 黑名单过期时间（秒），应与 Token 剩余有效期相同
        key_prefix: Redis Key 前缀
    """
    key = get_blacklist_key(jti, key_prefix)
    await RedisUtil.set(key, "1", ttl=ttl_seconds)


async def is_blacklisted(jti: str, key_prefix: str = "") -> bool:
    """
    检查 Token 是否在黑名单中。

    Args:
        jti: Token 的 JTI（JWT ID）
        key_prefix: Redis Key 前缀

    Returns:
        Token 是否在黑名单中
    """
    key = get_blacklist_key(jti, key_prefix)
    return await RedisUtil.exists(key)
