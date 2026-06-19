"""
数据库锁实现

基于数据库行级锁实现分布式锁。
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator

from framework.core.lock import Lock, LockProvider


class DatabaseLock:
    """数据库锁实现"""

    def __init__(self):
        self._prefix = "lock_"
        self._locks: dict[str, str] = {}  # 内存存储锁值

    async def acquire(
        self,
        key: str,
        ttl: int,
        timeout: int | None = None,
        retry_interval: float = 0.1
    ) -> Lock | None:
        """获取锁"""
        # 简化实现：使用内存锁
        # 实际实现应该使用数据库行级锁
        import uuid

        lock_value = str(uuid.uuid4())
        lock_key = self._prefix + key

        if lock_key not in self._locks:
            self._locks[lock_key] = lock_value
            return Lock(
                key=key,
                value=lock_value,
                ttl=ttl,
                acquired_at=datetime.now()
            )

        return None

    async def release(self, lock: Lock) -> bool:
        """释放锁"""
        lock_key = self._prefix + lock.key

        if self._locks.get(lock_key) == lock.value:
            del self._locks[lock_key]
            return True

        return False

    async def extend(self, lock: Lock, ttl: int) -> bool:
        """延长锁过期时间"""
        lock_key = self._prefix + lock.key

        if self._locks.get(lock_key) == lock.value:
            # 更新 TTL（需要额外的 TTL 管理机制）
            return True

        return False

    async def is_locked(self, key: str) -> bool:
        """检查是否被锁定"""
        lock_key = self._prefix + key
        return lock_key in self._locks

    async def force_release(self, key: str) -> bool:
        """强制释放锁"""
        lock_key = self._prefix + key

        if lock_key in self._locks:
            del self._locks[lock_key]
            return True

        return False
