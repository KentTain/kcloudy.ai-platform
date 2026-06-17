"""包含 'InMemoryStorage' 模型的模块."""

from typing import Any

from ai.components.graphrag.index.storage.file_pipeline_storage import (
    FilePipelineStorage,
)
from ai.components.graphrag.index.storage.typing import PipelineStorage


class MemoryPipelineStorage(FilePipelineStorage):
    """内存存储类定义."""

    _storage: dict[str, Any]

    def __init__(self):
        """初始化方法定义."""
        super().__init__(root_dir=".output")
        self._storage = {}

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
        return self._storage.get(key) or await super().get(key, as_bytes, encoding)

    async def set(
        self, key: str, value: str | bytes | None, encoding: str | None = None
    ) -> None:
        """
        设置给定键的值。

        Args:
            - key - 要设置值的键。
            - value - 要设置的值。
        """
        self._storage[key] = value

    async def has(self, key: str) -> bool:
        """
        如果给定键存在于存储中则返回 True。

        Args:
            - key - 要检查的键。

        Returns
        -------
            - output - 如果键存在于存储中则为 True,否则为 False。
        """
        return key in self._storage or await super().has(key)

    async def delete(self, key: str) -> None:
        """
        从存储中删除给定的键。

        Args:
            - key - 要删除的键。
        """
        del self._storage[key]

    async def clear(self) -> None:
        """清空存储."""
        self._storage.clear()

    def child(self, name: str | None) -> "PipelineStorage":
        """创建子存储实例."""
        return self


def create_memory_storage() -> PipelineStorage:
    """创建内存存储."""
    return MemoryPipelineStorage()
