"""包含 text_translate methods definition."""

from enum import Enum
from typing import Any, cast

import pandas as pd
from datashaper import (
    AsyncType,
    TableContainer,
    VerbCallbacks,
    VerbInput,
    derive_from_rows,
    verb,
)

from ai.components.graphrag.index.cache import PipelineCache

from .strategies.typing import TextTranslationStrategy


class TextTranslateStrategyType(str, Enum):
    """TextTranslateStrategyType 类定义."""

    openai = "openai"
    mock = "mock"

    def __repr__(self):
        """
        实现 __repr__ 协议方法。

        Returns:
            处理结果。
        """
        return f'"{self.value}"'


@verb(name="text_translate")
async def text_translate(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    text_column: str,
    to: str,
    strategy: dict[str, Any],
    async_mode: AsyncType = AsyncType.AsyncIO,
    **kwargs,
) -> TableContainer:
    """
    处理text_translate。

    Args:
        input (VerbInput): input 参数。
        cache (PipelineCache): cache 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        text_column (str): text_column 参数。
        to (str): to 参数。
        strategy (dict[str, Any]): strategy 参数。
        async_mode (AsyncType): async_mode 参数。
        kwargs: kwargs 参数。

    Returns:
        处理结果。
    """
    output_df = cast("pd.DataFrame", input.get_input())
    strategy_type = strategy["type"]
    strategy_args = {**strategy}
    strategy_exec = _load_strategy(strategy_type)

    async def run_strategy(row):
        """
        执行strategy。

        Args:
            row: row 参数。

        Returns:
            处理结果。
        """
        text = row[text_column]
        result = await strategy_exec(text, strategy_args, callbacks, cache)

        # If it is a single string, then return just the translation for that string
        if isinstance(text, str):
            return result.translations[0]

        # Otherwise, return a list of translations, one for each item in the input
        return list(result.translations)

    results = await derive_from_rows(
        output_df,
        run_strategy,
        callbacks,
        scheduling_type=async_mode,
        num_threads=kwargs.get("num_threads", 4),
    )
    output_df[to] = results
    return TableContainer(table=output_df)


def _load_strategy(strategy: TextTranslateStrategyType) -> TextTranslationStrategy:
    """
    加载load_strategy。

    Args:
        strategy (TextTranslateStrategyType): strategy 参数。

    Returns:
        处理结果。
    """
    match strategy:
        case TextTranslateStrategyType.openai:
            from .strategies.openai import run as run_openai

            return run_openai

        case TextTranslateStrategyType.mock:
            from .strategies.mock import run as run_mock

            return run_mock

        case _:
            msg = f"Unknown strategy: {strategy}"
            raise ValueError(msg)
