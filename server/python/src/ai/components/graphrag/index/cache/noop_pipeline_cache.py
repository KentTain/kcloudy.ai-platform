"""包含NoopPipelineCache实现的模块."""

from typing import Any

from ai.components.graphrag.index.cache.pipeline_cache import PipelineCache


class NoopPipelineCache(PipelineCache):
    """管道缓存的空操作实现,通常用于测试."""

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
        return None

    async def set(
        self, key: str, value: str | bytes | None, debug_data: dict | None = None
    ) -> None:
        """
        设置给定键的值。

        Args:
            - key - 要设置值的键。
            - value - 要设置的值。
        """

    async def has(self, key: str) -> bool:
        """
        如果给定的键存在于缓存中,则返回True。

        Args:
            - key - 要检查的键。

        Returns
        -------
            - output - 如果键存在于缓存中则返回True,否则返回False。
        """
        return False

    async def delete(self, key: str) -> None:
        """
        从缓存中删除给定的键。

        Args:
            - key - 要删除的键。
        """

    async def clear(self) -> None:
        """清除缓存."""

    def child(self, name: str) -> PipelineCache:
        """
        创建具有给定名称的子缓存。

        Args:
            - name - 创建子缓存时使用的名称。
        """
        return self
