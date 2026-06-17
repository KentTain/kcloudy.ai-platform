"""包含 ds_zip 方法定义的模块."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb


@verb(name="zip")
def zip_verb(
    input: VerbInput,
    to: str,
    columns: list[str],
    type: str | None = None,
    **_kwargs: dict,
) -> TableContainer:
    """
    将多个列压缩在一起。

    ## 用法
    TODO
    """
    table = cast("pd.DataFrame", input.get_input())
    if type is None:
        table[to] = list(zip(*[table[col] for col in columns], strict=True))

    # 这个有点特殊
    elif type == "dict":
        if len(columns) != 2:
            msg = f"字典类型需要恰好两列，但得到了 {columns}"
            raise ValueError(msg)
        key_col, value_col = columns

        results = []
        for _, row in table.iterrows():
            keys = row[key_col]
            values = row[value_col]
            output = {}
            if len(keys) != len(values):
                msg = f"期望相同数量的键和值，但得到 {len(keys)} 个键和 {len(values)} 个值"
                raise ValueError(msg)
            for idx, key in enumerate(keys):
                output[key] = values[idx]
            results.append(output)

        table[to] = results
    return TableContainer(table=table.reset_index(drop=True))
