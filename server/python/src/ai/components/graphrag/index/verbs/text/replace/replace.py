"""包含 replace and _apply_replacements methods."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from ai.components.graphrag.index.verbs.text.replace.typing import Replacement


@verb(name="text_replace")
def text_replace(
    input: VerbInput,
    column: str,
    to: str,
    replacements: list[dict[str, str]],
    **_kwargs: dict,
) -> TableContainer:
    """
    处理text_replace。

    Args:
        input (VerbInput): input 参数。
        column (str): column 参数。
        to (str): to 参数。
        replacements (list[dict[str, str]]): replacements 参数。
        _kwargs (dict): _kwargs 参数。

    Returns:
        处理结果。
    """
    output = cast("pd.DataFrame", input.get_input())
    parsed_replacements = [Replacement(**r) for r in replacements]
    output[to] = output[column].apply(
        lambda text: _apply_replacements(text, parsed_replacements)
    )
    return TableContainer(table=output)


def _apply_replacements(text: str, replacements: list[Replacement]) -> str:
    """
    处理apply_replacements。

    Args:
        text (str): text 参数。
        replacements (list[Replacement]): replacements 参数。

    Returns:
        处理结果。
    """
    for r in replacements:
        text = text.replace(r.pattern, r.replacement)
    return text
