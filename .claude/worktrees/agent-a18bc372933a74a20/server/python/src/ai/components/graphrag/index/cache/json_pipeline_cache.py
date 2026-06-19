"""包含'FilePipelineCache'模型的模块."""

import json
from typing import Any

from ai.components.graphrag.index.cache.pipeline_cache import PipelineCache
from ai.components.graphrag.index.storage import PipelineStorage


class JsonPipelineCache(PipelineCache):
    """文件管道缓存类定义."""

    _storage: PipelineStorage
    _encoding: str

    def __init__(self, storage: PipelineStorage, encoding="utf-8"):
        """初始化方法定义."""
        self._storage = storage
        self._encoding = encoding

    async def get(self, key: str) -> str | None:
        """获取方法定义."""
        if await self.has(key):
            try:
                data = await self._storage.get(key, encoding=self._encoding)
                data = json.loads(data)
            except UnicodeDecodeError:
                await self._storage.delete(key)
                return None
            except json.decoder.JSONDecodeError:
                await self._storage.delete(key)
                return None
            else:
                return data.get("result")

        return None

    async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
        """设置方法定义."""
        if value is None:
            return
        data = {"result": value, **(debug_data or {})}
        await self._storage.set(
            key, json.dumps(data, ensure_ascii=False), encoding=self._encoding
        )

    async def has(self, key: str) -> bool:
        """检查是否存在方法定义."""
        return await self._storage.has(key)

    async def delete(self, key: str) -> None:
        """删除方法定义."""
        if await self.has(key):
            await self._storage.delete(key)

    async def clear(self) -> None:
        """清除方法定义."""
        await self._storage.clear()

    def child(self, name: str) -> "JsonPipelineCache":
        """子级方法定义."""
        return JsonPipelineCache(self._storage.child(name), encoding=self._encoding)
