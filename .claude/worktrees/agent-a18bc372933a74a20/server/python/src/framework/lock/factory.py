"""
锁工厂

根据配置返回对应的锁实现。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framework.configs.settings import LockSettings
    from framework.core.lock import LockProvider


def get_lock_provider(config: "LockSettings") -> "LockProvider":
    """
    获取锁提供者

    Args:
        config: 锁配置

    Returns:
        LockProvider: 锁提供者实例

    Raises:
        ValueError: 不支持的锁类型
    """
    lock_type = config.provider.lower()

    match lock_type:
        case "redis":
            from framework.lock.impl.redis import RedisLock
            return RedisLock()
        case "sqlalchemy":
            from framework.lock.impl.sqlalchemy import DatabaseLock
            return DatabaseLock()
        case _:
            raise ValueError(f"不支持的锁类型: {lock_type}")
