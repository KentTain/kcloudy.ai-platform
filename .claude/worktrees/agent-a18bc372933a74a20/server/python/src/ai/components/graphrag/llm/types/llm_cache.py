"""
LLM 缓存接口定义

定义了 LLM 缓存系统的协议接口。
"""

from typing import Any, Protocol


class LLMCache(Protocol):
    """
    LLM 缓存接口

    定义了缓存系统必须实现的方法。
    """

    async def has(self, key: str) -> bool:
        """
        检查缓存中是否存在指定键的值

        Args:
            key: 缓存键

        Returns
        -------
            如果缓存中存在该键则返回 True,否则返回 False
        """
        ...

    async def get(self, key: str) -> Any | None:
        """
        从缓存中获取值

        Args:
            key: 缓存键

        Returns
        -------
            缓存的值,如果不存在则返回 None
        """
        ...

    async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
        """
        将值写入缓存

        Args:
            key: 缓存键
            value: 要缓存的值
            debug_data: 调试数据(可选),用于记录缓存相关的元信息
        """
        ...
