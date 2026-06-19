"""包含 'FileStorage' 和 'FilePipelineStorage' 模型的模块."""

import logging
import os
import re
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import aiofiles
from aiofiles.os import remove
from aiofiles.ospath import exists
from datashaper import Progress

from ai.components.graphrag.index.progress import ProgressReporter
from ai.components.graphrag.index.storage.typing import PipelineStorage

log = logging.getLogger(__name__)


class FilePipelineStorage(PipelineStorage):
    """文件存储类定义."""

    _root_dir: str
    _encoding: str

    def __init__(self, root_dir: str | None = None, encoding: str | None = None):
        """初始化方法定义."""
        self._root_dir = root_dir or ""
        self._encoding = encoding or "utf-8"
        Path(self._root_dir).mkdir(parents=True, exist_ok=True)

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressReporter | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """使用文件模式和自定义过滤函数在存储中查找文件."""

        def item_filter(item: dict[str, Any]) -> bool:
            """
            处理item_filter。

            Args:
                item (dict[str, Any]): item 参数。

            Returns:
                处理结果。
            """
            if file_filter is None:
                return True

            return all(re.match(value, item[key]) for key, value in file_filter.items())

        search_path = Path(self._root_dir) / (base_dir or "")
        log.info("search %s for files matching %s", search_path, file_pattern.pattern)
        all_files = list(search_path.rglob("**/*"))
        num_loaded = 0
        num_total = len(all_files)
        num_filtered = 0
        for file in all_files:
            match = file_pattern.match(f"{file}")
            if match:
                group = match.groupdict()
                if item_filter(group):
                    filename = f"{file}".replace(self._root_dir, "")
                    if filename.startswith(os.sep):
                        filename = filename[1:]
                    yield (filename, group)
                    num_loaded += 1
                    if max_count > 0 and num_loaded >= max_count:
                        break
                else:
                    num_filtered += 1
            else:
                num_filtered += 1
            if progress is not None:
                progress(_create_progress_status(num_loaded, num_filtered, num_total))

    async def get(
        self, key: str, as_bytes: bool | None = False, encoding: str | None = None
    ) -> Any:
        """获取方法定义."""
        file_path = join_path(self._root_dir, key)

        if await self.has(key):
            return await self._read_file(file_path, as_bytes, encoding)
        if await exists(key):
            # 查找键,因为它可能是从输入加载的新文件
            # 尚未写入存储
            return await self._read_file(key, as_bytes, encoding)

        return None

    async def _read_file(
        self,
        path: str | Path,
        as_bytes: bool | None = False,
        encoding: str | None = None,
    ) -> Any:
        """读取文件的内容."""
        read_type = "rb" if as_bytes else "r"
        encoding = None if as_bytes else (encoding or self._encoding)

        async with aiofiles.open(
            path,
            cast("Any", read_type),
            encoding=encoding,
        ) as f:
            return await f.read()

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """设置方法定义."""
        is_bytes = isinstance(value, bytes)
        write_type = "wb" if is_bytes else "w"
        encoding = None if is_bytes else encoding or self._encoding
        async with aiofiles.open(
            join_path(self._root_dir, key),
            cast("Any", write_type),
            encoding=encoding,
        ) as f:
            await f.write(value)

    async def has(self, key: str) -> bool:
        """Has 方法定义."""
        return await exists(join_path(self._root_dir, key))

    async def delete(self, key: str) -> None:
        """删除方法定义."""
        if await self.has(key):
            await remove(join_path(self._root_dir, key))

    async def clear(self) -> None:
        """清空方法定义."""
        for file in Path(self._root_dir).glob("*"):
            if file.is_dir():
                shutil.rmtree(file)
            else:
                file.unlink()

    def child(self, name: str | None) -> "PipelineStorage":
        """创建子存储实例."""
        if name is None:
            return self
        return FilePipelineStorage(str(Path(self._root_dir) / Path(name)))


def join_path(file_path: str, file_name: str) -> Path:
    """连接路径和文件。独立于操作系统."""
    return Path(file_path) / Path(file_name).parent / Path(file_name).name


def create_file_storage(out_dir: str | None) -> PipelineStorage:
    """创建基于文件的存储."""
    log.info("Creating file storage at %s", out_dir)
    return FilePipelineStorage(out_dir)


def _create_progress_status(
    num_loaded: int, num_filtered: int, num_total: int
) -> Progress:
    """
    创建progress_status。

    Args:
        num_loaded (int): num_loaded 参数。
        num_filtered (int): num_filtered 参数。
        num_total (int): num_total 参数。

    Returns:
        处理结果。
    """
    return Progress(
        total_items=num_total,
        completed_items=num_loaded + num_filtered,
        description=f"{num_loaded} files loaded ({num_filtered} filtered)",
    )
