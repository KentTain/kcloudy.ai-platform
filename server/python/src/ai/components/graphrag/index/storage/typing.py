"""包含 'PipelineStorage' 模型的模块."""

import re
from abc import ABCMeta, abstractmethod
from collections.abc import Iterator
from typing import Any

from ai.components.graphrag.index.progress import ProgressReporter


class PipelineStorage(metaclass=ABCMeta):
    """为管道提供存储接口。这是管道存储其输出数据的地方."""

    @abstractmethod
    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressReporter | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """使用文件模式和自定义过滤函数在存储中查找文件."""

    @abstractmethod
    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """
        获取给定键的值。

        Args:
            - key - 要获取值的键。
            - as_bytes - 是否将值作为字节返回。

        Returns
        -------
            - output - 给定键的值。
        """

    @abstractmethod
    async def set(
        self, key: str, value: str | bytes | None, encoding: str | None = None
    ) -> None:
        """
        设置给定键的值。

        Args:
            - key - 要设置值的键。
            - value - 要设置的值。
        """

    @abstractmethod
    async def has(self, key: str) -> bool:
        """
        如果给定键存在于存储中则返回 True。

        Args:
            - key - 要检查的键。

        Returns
        -------
            - output - 如果键存在于存储中则为 True,否则为 False。
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        从存储中删除给定的键。

        Args:
            - key - 要删除的键。
        """

    @abstractmethod
    async def clear(self) -> None:
        """清空存储."""

    @abstractmethod
    def child(self, name: str | None) -> "PipelineStorage":
        """创建子存储实例."""
