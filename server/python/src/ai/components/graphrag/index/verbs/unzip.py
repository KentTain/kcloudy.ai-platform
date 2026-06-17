"""包含 unzip 方法定义的模块."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb


# TODO: Check if this is already a thing
# Takes 1|(x,y)|b
# and converts to
# 1|x|y|b
@verb(name="unzip")
def unzip(
    input: VerbInput, column: str, to: list[str], **_kwargs: dict
) -> TableContainer:
    """将包含元组的列解包为多个列."""
    table = cast("pd.DataFrame", input.get_input())

    table[to] = pd.DataFrame(table[column].tolist(), index=table.index)

    return TableContainer(table=table)
