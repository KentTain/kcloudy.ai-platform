"""包含 merge 和 _merge_json 方法定义的模块."""

import logging
from enum import Enum
from typing import Any, cast

import pandas as pd
from datashaper import TableContainer, VerbInput, VerbResult, verb
from datashaper.engine.verbs.merge import merge as ds_merge

log = logging.getLogger(__name__)


class MergeStrategyType(str, Enum):
    """封装组件图谱检索增强生成中的MergeStrategyType逻辑。"""

    json = "json"
    datashaper = "datashaper"

    def __repr__(self):
        """
        实现 __repr__ 协议方法。

        Returns:
            处理结果。
        """
        return f'"{self.value}"'


# TODO: This thing is kinda gross
# Also, it diverges from the original aggregate verb, since it doesn't support the same syntax
@verb(name="merge_override")
def merge(
    input: VerbInput,
    to: str,
    columns: list[str],
    strategy: MergeStrategyType = MergeStrategyType.datashaper,
    delimiter: str = "",
    preserve_source: bool = False,
    unhot: bool = False,
    prefix: str = "",
    **_kwargs: dict,
) -> TableContainer | VerbResult:
    """合并方法定义."""
    output: pd.DataFrame
    match strategy:
        case MergeStrategyType.json:
            output = _merge_json(input, to, columns)
            filtered_list: list[str] = []

            for col in output.columns:
                try:
                    columns.index(col)
                except ValueError:
                    log.exception("Column %s not found in input columns", col)
                    filtered_list.append(col)

            if not preserve_source:
                output = cast("Any", output[filtered_list])
            return TableContainer(table=output.reset_index())
        case _:
            return ds_merge(
                input, to, columns, strategy, delimiter, preserve_source, unhot, prefix
            )


def _merge_json(
    input: VerbInput,
    to: str,
    columns: list[str],
) -> pd.DataFrame:
    """
    合并merge_json。

    Args:
        input (VerbInput): input 参数。
        to (str): to 参数。
        columns (list[str]): columns 参数。

    Returns:
        处理结果。
    """
    input_table = cast("pd.DataFrame", input.get_input())
    output = input_table
    output[to] = output[columns].apply(
        lambda row: ({**row}),
        axis=1,
    )
    return output
