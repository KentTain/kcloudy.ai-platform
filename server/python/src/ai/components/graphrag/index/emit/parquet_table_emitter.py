"""ParquetTableEmitter模块."""

import logging
import traceback

import pandas as pd
from pyarrow.lib import ArrowInvalid, ArrowTypeError

from ai.components.graphrag.index.emit.table_emitter import TableEmitter
from ai.components.graphrag.index.storage import PipelineStorage
from ai.components.graphrag.index.typing import ErrorHandlerFn

log = logging.getLogger(__name__)


class ParquetTableEmitter(TableEmitter):
    """ParquetTableEmitter类."""

    _storage: PipelineStorage
    _on_error: ErrorHandlerFn

    def __init__(
        self,
        storage: PipelineStorage,
        on_error: ErrorHandlerFn,
    ):
        """创建一个新的Parquet表格发送器."""
        self._storage = storage
        self._on_error = on_error

    async def emit(self, name: str, data: pd.DataFrame) -> None:
        """将数据帧发送到存储."""
        filename = f"{name}.parquet"
        log.info("emitting parquet table %s", filename)
        try:
            if "findings" in data.columns:
                data.findings = data.findings.astype(str)
            await self._storage.set(filename, data.to_parquet())
        except ArrowTypeError as e:
            log.exception("Error while emitting parquet table")
            self._on_error(
                e,
                traceback.format_exc(),
                None,
            )
            raise e
        except ArrowInvalid as e:
            log.exception("Error while emitting parquet table")
            self._on_error(
                e,
                traceback.format_exc(),
                None,
            )
            raise e
