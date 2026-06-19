"""包含 the text_split method definition."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb


@verb(name="text_split")
def text_split(
    input: VerbInput,
    column: str,
    to: str,
    separator: str = ",",
    **_kwargs: dict,
) -> TableContainer:
    """
    处理text_split。

    Args:
        input (VerbInput): input 参数。
        column (str): column 参数。
        to (str): to 参数。
        separator (str): separator 参数。
        _kwargs (dict): _kwargs 参数。

    Returns:
        处理结果。
    """
    output = text_split_df(
        cast("pd.DataFrame", input.get_input()), column, to, separator
    )
    return TableContainer(table=output)


def text_split_df(
    input: pd.DataFrame, column: str, to: str, separator: str = ","
) -> pd.DataFrame:
    """
    处理text_split_df。

    Args:
        input (pd.DataFrame): input 参数。
        column (str): column 参数。
        to (str): to 参数。
        separator (str): separator 参数。

    Returns:
        处理结果。
    """
    output = input

    def _apply_split(row):
        """
        处理apply_split。

        Args:
            row: row 参数。

        Returns:
            处理结果。
        """
        if row[column] is None or isinstance(row[column], list):
            return row[column]
        if row[column] == "":
            return []
        if not isinstance(row[column], str):
            message = f"Expected {column} to be a string, but got {type(row[column])}"
            raise TypeError(message)
        return row[column].split(separator)

    output[to] = output.apply(_apply_split, axis=1)
    return output
