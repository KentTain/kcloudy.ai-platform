"""表格发送器工厂."""

from ai.components.graphrag.index.emit.csv_table_emitter import CSVTableEmitter
from ai.components.graphrag.index.emit.json_table_emitter import JsonTableEmitter
from ai.components.graphrag.index.emit.parquet_table_emitter import (
    ParquetTableEmitter,
)
from ai.components.graphrag.index.emit.table_emitter import TableEmitter
from ai.components.graphrag.index.emit.types import TableEmitterType
from ai.components.graphrag.index.storage import PipelineStorage
from ai.components.graphrag.index.typing import ErrorHandlerFn


def create_table_emitter(
    emitter_type: TableEmitterType, storage: PipelineStorage, on_error: ErrorHandlerFn
) -> TableEmitter:
    """根据指定的类型创建表格发送器."""
    match emitter_type:
        case TableEmitterType.Json:
            return JsonTableEmitter(storage)
        case TableEmitterType.Parquet:
            return ParquetTableEmitter(storage, on_error)
        case TableEmitterType.CSV:
            return CSVTableEmitter(storage)
        case _:
            msg = f"Unsupported table emitter type: {emitter_type}"
            raise ValueError(msg)


def create_table_emitters(
    emitter_types: list[TableEmitterType],
    storage: PipelineStorage,
    on_error: ErrorHandlerFn,
) -> list[TableEmitter]:
    """根据指定的类型创建表格发送器列表."""
    return [
        create_table_emitter(emitter_type, storage, on_error)
        for emitter_type in emitter_types
    ]
