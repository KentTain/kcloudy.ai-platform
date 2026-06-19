"""
锁接口定义

使用 Python Protocol 定义统一的分布式锁接口。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass
class Lock:
    """锁对象"""

    key: str
    """锁键名"""

    value: str
    """锁值（用于验证所有权）"""

    ttl: int
    """过期时间（秒）"""

    acquired_at: datetime = field(default_factory=datetime.now)
    """获取时间"""

    metadata: dict = field(default_factory=dict)
    """元数据"""


@runtime_checkable
class LockProvider(Protocol):
    """
    锁提供者协议

    定义统一的分布式锁接口，支持 Redis 等实现。
    """

    async def acquire(
        self,
        key: str,
        ttl: int,
        timeout: int | None = None,
        retry_interval: float = 0.1
    ) -> Lock | None:
        """
        获取锁

        Args:
            key: 锁键名
            ttl: 过期时间（秒）
            timeout: 等待超时（秒），None 表示不等待
            retry_interval: 重试间隔（秒）

        Returns:
            Lock | None: 锁对象，获取失败返回 None
        """
        ...

    async def release(self, lock: Lock) -> bool:
        """
        释放锁

        Args:
            lock: 锁对象

        Returns:
            bool: 是否成功
        """
        ...

    async def extend(self, lock: Lock, ttl: int) -> bool:
        """
        延长锁过期时间

        Args:
            lock: 锁对象
            ttl: 新的过期时间（秒）

        Returns:
            bool: 是否成功
        """
        ...

    async def is_locked(self, key: str) -> bool:
        """
        检查是否被锁定

        Args:
            key: 锁键名

        Returns:
            bool: 是否被锁定
        """
        ...

    async def force_release(self, key: str) -> bool:
        """
        强制释放锁（不验证所有权）

        Args:
            key: 锁键名

        Returns:
            bool: 是否成功
        """
        ...
