"""包含 spread_json 方法定义的模块."""

import logging

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from ai.components.graphrag.index.utils import is_null

# TODO: Check if this is already a thing
DEFAULT_COPY = ["level"]


@verb(name="spread_json")
def spread_json(
    input: VerbInput,
    column: str,
    copy: list[str] | None = None,
    **_kwargs: dict,
) -> TableContainer:
    """
    将包含元组的列解包为多个列。

    id|json|b
    1|{"x":5,"y":6}|b

    转换为

    id|x|y|b
    --------
    1|5|6|b
    """
    if copy is None:
        copy = DEFAULT_COPY
    data = input.get_input()

    results = []
    for _, row in data.iterrows():
        try:
            cleaned_row = {col: row[col] for col in copy}
            rest_row = row[column] if row[column] is not None else {}

            if is_null(rest_row):
                rest_row = {}

            results.append({**cleaned_row, **rest_row})  # type: ignore
        except Exception:
            logging.exception("展开行时出错: %s", row)
            raise
    data = pd.DataFrame(results, index=data.index)

    return TableContainer(table=data)
