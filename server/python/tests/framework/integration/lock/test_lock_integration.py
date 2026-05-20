"""
Redis 分布式锁集成测试

测试 RedisLock 与真实 Redis 服务的交互。
使用 @pytest.mark.integration 标记。
"""

import asyncio

import pytest
import pytest_asyncio

from framework.cache.redis_util import RedisUtil
from framework.lock.impl.redis import RedisLock
from framework.core.lock import Lock


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def redis_lock(redis_client):
    """Redis 分布式锁实例"""
    return RedisLock()


@pytest_asyncio.fixture
async def cleanup_lock(redis_client, redis_key_prefix):
    """测试后清理锁"""
    lock_key = f"{redis_key_prefix}lock"
    yield lock_key
    # 确保清理锁
    await redis_client.delete(f"lock:{lock_key}")


class TestRedisLockAcquireRelease:
    """Redis 分布式锁获取与释放测试"""

    @pytest.mark.asyncio
    async def test_acquire_success(self, redis_lock, cleanup_lock):
        """
        场景：锁获取与释放
        WHEN: 调用 acquire 获取锁成功
        THEN: 锁状态正确，释放后其他客户端可获取
        """
        lock_key = cleanup_lock

        # 获取锁
        lock = await redis_lock.acquire(lock_key, ttl=30)
        assert lock is not None
        assert lock.key == lock_key
        assert lock.ttl == 30
        assert lock.value is not None

        # 验证锁已存在
        is_locked = await redis_lock.is_locked(lock_key)
        assert is_locked is True

        # 释放锁
        released = await redis_lock.release(lock)
        assert released is True

        # 验证锁已释放
        is_locked = await redis_lock.is_locked(lock_key)
        assert is_locked is False

    @pytest.mark.asyncio
    async def test_release_by_wrong_owner_fails(self, redis_lock, cleanup_lock):
        """
        场景：错误持有者释放锁
        WHEN: 非锁持有者尝试释放锁
        THEN: 释放失败
        """
        lock_key = cleanup_lock

        # 获取锁
        lock = await redis_lock.acquire(lock_key, ttl=30)
        assert lock is not None

        # 使用错误的值尝试释放
        fake_lock = Lock(key=lock_key, value="wrong_value", ttl=30)
        released = await redis_lock.release(fake_lock)
        assert released is False

        # 锁仍然存在
        is_locked = await redis_lock.is_locked(lock_key)
        assert is_locked is True

        # 正确释放
        await redis_lock.release(lock)

    @pytest.mark.asyncio
    async def test_acquire_with_timeout(self, redis_lock, cleanup_lock):
        """
        场景：带超时的锁获取
        WHEN: 锁被其他客户端持有，等待超时
        THEN: 超时后返回 None
        """
        lock_key = cleanup_lock

        # 第一次获取锁
        lock1 = await redis_lock.acquire(lock_key, ttl=30)
        assert lock1 is not None

        # 尝试获取同一把锁，设置超时
        lock2 = await redis_lock.acquire(lock_key, ttl=30, timeout=1)
        assert lock2 is None

        # 释放第一把锁
        await redis_lock.release(lock1)


class TestRedisLockTimeout:
    """Redis 分布式锁超时测试"""

    @pytest.mark.asyncio
    async def test_lock_auto_expire(self, redis_lock, cleanup_lock):
        """
        场景：锁超时
        WHEN: 设置锁的 TTL 过期
        THEN: 锁自动释放
        """
        lock_key = cleanup_lock

        # 获取锁，设置短 TTL
        lock = await redis_lock.acquire(lock_key, ttl=1)
        assert lock is not None

        # 验证锁存在
        assert await redis_lock.is_locked(lock_key)

        # 等待锁过期
        await asyncio.sleep(1.5)

        # 锁应该已自动释放
        is_locked = await redis_lock.is_locked(lock_key)
        assert is_locked is False


class TestRedisLockExtend:
    """Redis 分布式锁延长测试"""

    @pytest.mark.asyncio
    async def test_extend_success(self, redis_lock, cleanup_lock):
        """
        场景：锁延长
        WHEN: 调用 extend 延长锁的 TTL
        THEN: 锁的过期时间成功延长
        """
        lock_key = cleanup_lock

        # 获取锁
        lock = await redis_lock.acquire(lock_key, ttl=5)
        assert lock is not None

        # 延长锁
        extended = await redis_lock.extend(lock, ttl=10)
        assert extended is True

        # 验证锁仍然存在
        assert await redis_lock.is_locked(lock_key)

        # 清理
        await redis_lock.release(lock)

    @pytest.mark.asyncio
    async def test_extend_expired_lock_fails(self, redis_lock, cleanup_lock):
        """
        场景：延长已过期的锁
        WHEN: 锁已过期，尝试延长
        THEN: 延长失败
        """
        lock_key = cleanup_lock

        # 获取锁，设置短 TTL
        lock = await redis_lock.acquire(lock_key, ttl=1)
        assert lock is not None

        # 等待锁过期
        await asyncio.sleep(1.5)

        # 尝试延长已过期的锁
        extended = await redis_lock.extend(lock, ttl=10)
        assert extended is False


class TestRedisLockMutex:
    """Redis 分布式锁互斥访问测试"""

    @pytest.mark.asyncio
    async def test_mutex_access(self, redis_lock, cleanup_lock):
        """
        场景：互斥访问
        WHEN: 一个客户端持有锁
        THEN: 其他客户端无法同时获取同一把锁
        """
        lock_key = cleanup_lock

        # 第一个客户端获取锁
        lock1 = await redis_lock.acquire(lock_key, ttl=30)
        assert lock1 is not None

        # 第二个客户端尝试获取同一把锁（不等待）
        lock2 = await redis_lock.acquire(lock_key, ttl=30, timeout=0)
        assert lock2 is None

        # 释放第一把锁
        await redis_lock.release(lock1)

        # 现在第二个客户端可以获取锁
        lock2 = await redis_lock.acquire(lock_key, ttl=30)
        assert lock2 is not None

        # 清理
        await redis_lock.release(lock2)

    @pytest.mark.asyncio
    async def test_force_release(self, redis_lock, cleanup_lock):
        """
        场景：强制释放锁
        WHEN: 调用 force_release 强制释放锁
        THEN: 锁被释放，无论持有者是谁
        """
        lock_key = cleanup_lock

        # 获取锁
        lock = await redis_lock.acquire(lock_key, ttl=30)
        assert lock is not None

        # 强制释放
        released = await redis_lock.force_release(lock_key)
        assert released is True

        # 锁已不存在
        assert await redis_lock.is_locked(lock_key) is False


class TestRedisLockContext:
    """Redis 分布式锁上下文管理器测试"""

    @pytest.mark.asyncio
    async def test_context_manager(self, redis_lock, cleanup_lock):
        """
        场景：上下文管理器
        WHEN: 使用 async with 获取锁
        THEN: 退出上下文时自动释放锁
        """
        lock_key = cleanup_lock

        async with redis_lock.acquire_context(lock_key, ttl=30) as lock:
            assert lock is not None
            assert await redis_lock.is_locked(lock_key)

        # 退出上下文后锁应释放
        assert not await redis_lock.is_locked(lock_key)

    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self, redis_lock, cleanup_lock):
        """
        场景：上下文管理器异常处理
        WHEN: 上下文中发生异常
        THEN: 锁仍然被正确释放
        """
        lock_key = cleanup_lock

        try:
            async with redis_lock.acquire_context(lock_key, ttl=30) as lock:
                assert lock is not None
                raise ValueError("Test exception")
        except ValueError:
            pass

        # 异常后锁应释放
        assert not await redis_lock.is_locked(lock_key)
