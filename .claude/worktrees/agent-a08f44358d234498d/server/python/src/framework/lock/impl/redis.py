"""
Redis 分布式锁实现
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from framework.core.lock import Lock, LockProvider
from framework.cache.redis_util import RedisUtil


# Lua 脚本：释放锁（仅当值匹配时）
RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

# Lua 脚本：延长锁（仅当值匹配时）
EXTEND_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("expire", KEYS[1], ARGV[2])
else
    return 0
end
"""


class RedisLock:
    """Redis 分布式锁实现"""

    def __init__(self):
        self._prefix = "lock:"

    def _get_lock_key(self, key: str) -> str:
        """获取锁键名"""
        return f"{self._prefix}{key}"

    def _generate_value(self) -> str:
        """生成锁值"""
        return str(uuid.uuid4())

    async def acquire(
        self,
        key: str,
        ttl: int,
        timeout: int | None = None,
        retry_interval: float = 0.1
    ) -> Lock | None:
        """获取锁"""
        lock_key = self._get_lock_key(key)
        lock_value = self._generate_value()

        start_time = datetime.now()

        while True:
            # 尝试获取锁
            success = await RedisUtil.set(lock_key, lock_value, nx=True, ttl=ttl)

            if success:
                return Lock(
                    key=key,
                    value=lock_value,
                    ttl=ttl,
                    acquired_at=datetime.now()
                )

            # 检查超时
            if timeout is not None:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= timeout:
                    return None

            # 等待重试
            await asyncio.sleep(retry_interval)

    async def release(self, lock: Lock) -> bool:
        """释放锁"""
        lock_key = self._get_lock_key(lock.key)

        # 使用 Lua 脚本确保原子性
        result = await RedisUtil.eval(
            RELEASE_SCRIPT,
            1,
            lock_key,
            lock.value
        )

        return bool(result)

    async def extend(self, lock: Lock, ttl: int) -> bool:
        """延长锁过期时间"""
        lock_key = self._get_lock_key(lock.key)

        # 使用 Lua 脚本确保原子性
        result = await RedisUtil.eval(
            EXTEND_SCRIPT,
            1,
            lock_key,
            lock.value,
            str(ttl)
        )

        return bool(result)

    async def is_locked(self, key: str) -> bool:
        """检查是否被锁定"""
        lock_key = self._get_lock_key(key)
        return await RedisUtil.exists(lock_key)

    async def force_release(self, key: str) -> bool:
        """强制释放锁"""
        lock_key = self._get_lock_key(key)
        return await RedisUtil.delete(lock_key) > 0

    @asynccontextmanager
    async def acquire_context(
        self,
        key: str,
        ttl: int,
        timeout: int | None = None
    ) -> AsyncGenerator[Lock | None, None]:
        """
        上下文管理器获取锁

        Args:
            key: 锁键名
            ttl: 过期时间
            timeout: 等待超时

        Yields:
            Lock | None: 锁对象
        """
        lock = await self.acquire(key, ttl, timeout)
        try:
            yield lock
        finally:
            if lock:
                await self.release(lock)
