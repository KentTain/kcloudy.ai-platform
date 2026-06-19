"""表格发送器类型."""

from enum import Enum


class TableEmitterType(str, Enum):
    """表格发送器类型."""

    Json = "json"
    Parquet = "parquet"
    CSV = "csv"
