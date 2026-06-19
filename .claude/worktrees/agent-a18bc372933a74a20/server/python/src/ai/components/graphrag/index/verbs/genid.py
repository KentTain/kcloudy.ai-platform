"""包含 genid 方法定义的模块."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from ai.components.graphrag.index.utils import gen_md5_hash


@verb(name="genid")
def genid(
    input: VerbInput,
    to: str,
    method: str = "md5_hash",
    hash: list[str] = [],
    **_kwargs: dict,
) -> TableContainer:
    """
    为表格数据中的每一行生成唯一 ID。

    ## 用法
    ### json
    ```json
    {
        "verb": "genid",
        "args": {
            "to": "id_output_column_name", /* 输出 ID 的目标列名 */
            "method": "md5_hash", /* 用于生成 ID 的方法 */
            "hash": ["list", "of", "column", "names"] /* 仅在使用 md5_hash 时需要 */,
            "seed": 034324 /* 与 UUID 一起使用的随机种子 */
        }
    }
    ```

    ### yaml
    ```yaml
    verb: genid
    args:
        to: id_output_column_name
        method: md5_hash
        hash:
            - list
            - of
            - column
            - names
        seed: 034324
    ```
    """
    data = cast("pd.DataFrame", input.source.table)

    if method == "md5_hash":
        if len(hash) == 0:
            msg = '必须指定 "hash" 列才能使用 md5_hash 方法'
            raise ValueError(msg)

        data[to] = data.apply(lambda row: gen_md5_hash(row, hash), axis=1)
    elif method == "increment":
        data[to] = data.index + 1
    else:
        msg = f"未知的方法 {method}"
        raise ValueError(msg)
    return TableContainer(table=data)
