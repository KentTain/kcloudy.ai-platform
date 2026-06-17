"""包含'PipelineCache'模型的模块."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any


class PipelineCache(metaclass=ABCMeta):
    """为管道提供缓存接口."""

    @abstractmethod
    async def get(self, key: str) -> Any:
        """
        获取给定键的值。

        Args:
            - key - 要获取值的键。
            - as_bytes - 是否以字节形式返回值。

        Returns
        -------
            - output - 给定键的值。
        """

    @abstractmethod
    async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
        """
        设置给定键的值。

        Args:
            - key - 要设置值的键。
            - value - 要设置的值。
        """

    @abstractmethod
    async def has(self, key: str) -> bool:
        """
        如果给定的键存在于缓存中,则返回True。

        Args:
            - key - 要检查的键。

        Returns
        -------
            - output - 如果键存在于缓存中则返回True,否则返回False。
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        从缓存中删除给定的键。

        Args:
            - key - 要删除的键。
        """

    @abstractmethod
    async def clear(self) -> None:
        """清除缓存."""

    @abstractmethod
    def child(self, name: str) -> PipelineCache:
        """
        创建具有给定名称的子缓存。

        Args:
            - name - 创建子缓存时使用的名称。
        """
