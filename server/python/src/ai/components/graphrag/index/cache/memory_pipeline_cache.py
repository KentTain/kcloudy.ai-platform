"""包含'InMemoryCache'模型的模块."""

from typing import Any

from ai.components.graphrag.index.cache.pipeline_cache import PipelineCache


class InMemoryCache(PipelineCache):
    """内存缓存类定义."""

    _cache: dict[str, Any]
    _name: str

    def __init__(self, name: str | None = None):
        """初始化方法定义."""
        self._cache = {}
        self._name = name or ""

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
        key = self._create_cache_key(key)
        return self._cache.get(key)

    async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
        """
        设置给定键的值。

        Args:
            - key - 要设置值的键。
            - value - 要设置的值。
        """
        key = self._create_cache_key(key)
        self._cache[key] = value

    async def has(self, key: str) -> bool:
        """
        如果给定的键存在于存储中,则返回True。

        Args:
            - key - 要检查的键。

        Returns
        -------
            - output - 如果键存在于存储中则返回True,否则返回False。
        """
        key = self._create_cache_key(key)
        return key in self._cache

    async def delete(self, key: str) -> None:
        """
        从存储中删除给定的键。

        Args:
            - key - 要删除的键。
        """
        key = self._create_cache_key(key)
        del self._cache[key]

    async def clear(self) -> None:
        """清除存储."""
        self._cache.clear()

    def child(self, name: str) -> PipelineCache:
        """创建具有给定名称的子缓存."""
        return InMemoryCache(name)

    def _create_cache_key(self, key: str) -> str:
        """为给定的键创建缓存键."""
        return f"{self._name}{key}"


def create_memory_cache() -> PipelineCache:
    """创建内存缓存."""
    return InMemoryCache()
