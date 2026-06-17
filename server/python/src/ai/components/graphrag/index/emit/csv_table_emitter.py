"""CSVTableEmitter模块."""

import logging

import pandas as pd

from ai.components.graphrag.index.emit.table_emitter import TableEmitter
from ai.components.graphrag.index.storage import PipelineStorage

log = logging.getLogger(__name__)


class CSVTableEmitter(TableEmitter):
    """CSVTableEmitter类."""

    _storage: PipelineStorage

    def __init__(self, storage: PipelineStorage):
        """创建一个新的CSV表格发送器."""
        self._storage = storage

    async def emit(self, name: str, data: pd.DataFrame) -> None:
        """将数据帧发送到存储."""
        filename = f"{name}.csv"
        log.info("emitting CSV table %s", filename)
        await self._storage.set(
            filename,
            data.to_csv(),
        )
