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

# 内存会话存储（当 Redis 不可用时使用）
_memory_sessions: dict[str, dict[str, Any]] = {}
_memory_blacklist: dict[str, float] = {}


def _is_redis_available() -> bool:
    """检查 Redis 是否可用"""
    return RedisUtil._client is not None


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
    tenant_id: str | None = None,
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

    if _is_redis_available():
        # 计算 TTL
        ttl_seconds = int(
            (ttl or timedelta(days=DEFAULT_SESSION_TTL_DAYS)).total_seconds()
        )

        # 存储到 Redis
        key = get_session_key(session_id, key_prefix)
        await RedisUtil.set(key, json.dumps(session_data), ttl=ttl_seconds)
    else:
        # 存储到内存
        _memory_sessions[session_id] = session_data

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
        会话数据字典，不存在则返回 None
    """
    if _is_redis_available():
        key = get_session_key(session_id, key_prefix)
        data = await RedisUtil.get(key)
        if data:
            return json.loads(data)
        return None
    else:
        return _memory_sessions.get(session_id)


async def delete_session(session_id: str, key_prefix: str = "") -> None:
    """
    删除会话。

    Args:
        session_id: 会话 ID
        key_prefix: Redis Key 前缀
    """
    if _is_redis_available():
        key = get_session_key(session_id, key_prefix)
        await RedisUtil.delete(key)
    else:
        _memory_sessions.pop(session_id, None)


async def delete_user_sessions(user_id: str, key_prefix: str = "") -> int:
    """
    删除用户所有会话。

    Args:
        user_id: 用户 ID
        key_prefix: Redis Key 前缀

    Returns:
        int: 删除的会话数量
    """
    deleted_count = 0

    if _is_redis_available():
        # 查找所有会话 key
        pattern = f"{key_prefix}session:*"
        keys = await RedisUtil.keys(pattern)

        for key in keys:
            data = await RedisUtil.get(key)
            if data:
                try:
                    session_data = json.loads(data)
                    if session_data.get("user_id") == user_id:
                        await RedisUtil.delete(key)
                        deleted_count += 1
                except json.JSONDecodeError:
                    continue
    else:
        # 从内存中删除
        sessions_to_delete = [
            sid
            for sid, data in _memory_sessions.items()
            if data.get("user_id") == user_id
        ]
        for sid in sessions_to_delete:
            del _memory_sessions[sid]
            deleted_count += 1

    return deleted_count


async def add_to_blacklist(jti: str, ttl_seconds: int, key_prefix: str = "") -> None:
    """
    将 Token 加入黑名单。

    Args:
        jti: Token 的 JTI（JWT ID）
        ttl_seconds: 黑名单过期时间（秒）
        key_prefix: Redis Key 前缀
    """
    if _is_redis_available():
        key = get_blacklist_key(jti, key_prefix)
        await RedisUtil.set(key, "1", ttl=ttl_seconds)
    else:
        _memory_blacklist[jti] = datetime.now(timezone.utc).timestamp() + ttl_seconds


async def is_blacklisted(jti: str, key_prefix: str = "") -> bool:
    """
    检查 Token 是否在黑名单中。

    Args:
        jti: Token 的 JTI（JWT ID）
        key_prefix: Redis Key 前缀

    Returns:
        是否在黑名单中
    """
    if _is_redis_available():
        key = get_blacklist_key(jti, key_prefix)
        return await RedisUtil.get(key) is not None
    else:
        expire_time = _memory_blacklist.get(jti)
        if expire_time is None:
            return False
        # 检查是否过期
        if datetime.now(timezone.utc).timestamp() > expire_time:
            del _memory_blacklist[jti]
            return False
        return True
