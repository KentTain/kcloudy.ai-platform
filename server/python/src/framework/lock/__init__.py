"""
锁模块

提供 Redis 等分布式锁实现。
"""

from framework.lock.factory import get_lock_provider

__all__ = [
    "get_lock_provider",
]
