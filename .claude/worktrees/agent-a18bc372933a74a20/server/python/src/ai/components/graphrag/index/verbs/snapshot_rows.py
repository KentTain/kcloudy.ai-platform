"""包含 'FormatSpecifier' 模型的模块."""

import json
from dataclasses import dataclass
from typing import Any

from datashaper import TableContainer, VerbInput, verb

from ai.components.graphrag.index.storage import PipelineStorage


@dataclass
class FormatSpecifier:
    """格式说明符类定义."""

    format: str
    extension: str


@verb(name="snapshot_rows")
async def snapshot_rows(
    input: VerbInput,
    column: str | None,
    base_name: str,
    storage: PipelineStorage,
    formats: list[str | dict[str, Any]],
    row_name_column: str | None = None,
    **_kwargs: dict,
) -> TableContainer:
    """对表格数据进行逐行快照."""
    data = input.get_input()
    parsed_formats = _parse_formats(formats)
    num_rows = len(data)

    def get_row_name(row: Any, row_idx: Any):
        """
        获取row_name。

        Args:
            row (Any): row 参数。
            row_idx (Any): row_idx 参数。

        Returns:
            处理结果。
        """
        if row_name_column is None:
            if num_rows == 1:
                return base_name
            return f"{base_name}.{row_idx}"
        return f"{base_name}.{row[row_name_column]}"

    for row_idx, row in data.iterrows():
        for fmt in parsed_formats:
            row_name = get_row_name(row, row_idx)
            extension = fmt.extension
            if fmt.format == "json":
                await storage.set(
                    f"{row_name}.{extension}",
                    (
                        json.dumps(row[column], ensure_ascii=False)
                        if column is not None
                        else json.dumps(row.to_dict(), ensure_ascii=False)
                    ),
                )
            elif fmt.format == "text":
                if column is None:
                    msg = "text 格式必须指定 column"
                    raise ValueError(msg)
                await storage.set(f"{row_name}.{extension}", str(row[column]))

    return TableContainer(table=data)


def _parse_formats(formats: list[str | dict[str, Any]]) -> list[FormatSpecifier]:
    """将格式解析为 FormatSpecifier 列表."""
    return [
        (
            FormatSpecifier(**fmt)
            if isinstance(fmt, dict)
            else FormatSpecifier(format=fmt, extension=_get_format_extension(fmt))
        )
        for fmt in formats
    ]


def _get_format_extension(fmt: str) -> str:
    """获取给定格式的文件扩展名."""
    if fmt == "json":
        return "json"
    if fmt == "text":
        return "txt"
    if fmt == "parquet":
        return "parquet"
    if fmt == "csv":
        return "csv"
    msg = f"未知格式: {fmt}"
    raise ValueError(msg)
