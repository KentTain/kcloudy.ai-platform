"""用于将表格发送到目标的TableEmitter协议."""

from typing import Protocol

import pandas as pd


class TableEmitter(Protocol):
    """用于将表格发送到目标的TableEmitter协议."""

    async def emit(self, name: str, data: pd.DataFrame) -> None:
        """将数据帧发送到存储."""
