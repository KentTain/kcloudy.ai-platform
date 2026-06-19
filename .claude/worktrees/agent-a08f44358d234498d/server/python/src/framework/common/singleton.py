"""
单例模式实现
"""

import abc
from typing import Any


class Singleton(abc.ABCMeta, type):
    """单例元类，用于确保一个类只有一个实例"""

    _instances: dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class AbstractSingleton(abc.ABC, metaclass=Singleton):
    """抽象单例类"""

    pass
