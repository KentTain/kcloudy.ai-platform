"""包含 _get_num_total, chunk, run_strategy and load_strategy methods definitions."""

from enum import Enum
from typing import Any, cast

import pandas as pd
from datashaper import (
    ProgressTicker,
    TableContainer,
    VerbCallbacks,
    VerbInput,
    progress_ticker,
    verb,
)

from ai.components.graphrag.index.verbs.text.chunk.typing import ChunkInput

from .strategies.typing import ChunkStrategy


def _get_num_total(output: pd.DataFrame, column: str) -> int:
    """
    获取num_total。

    Args:
        output (pd.DataFrame): output 参数。
        column (str): column 参数。

    Returns:
        处理结果。
    """
    num_total = 0
    for row in output[column]:
        if isinstance(row, str):
            num_total += 1
        else:
            num_total += len(row)
    return num_total


class ChunkStrategyType(str, Enum):
    """ChunkStrategy 类定义."""

    tokens = "tokens"
    sentence = "sentence"

    def __repr__(self):
        """
        实现 __repr__ 协议方法。

        Returns:
            处理结果。
        """
        return f'"{self.value}"'


@verb(name="chunk")
def chunk(
    input: VerbInput,
    column: str,
    to: str,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any] | None = None,
    **_kwargs,
) -> TableContainer:
    """
    分块chunk。

    Args:
        input (VerbInput): input 参数。
        column (str): column 参数。
        to (str): to 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        strategy (dict[str, Any] | None): strategy 参数。
        _kwargs: _kwargs 参数。

    Returns:
        处理结果。
    """
    if strategy is None:
        strategy = {}
    output = cast("pd.DataFrame", input.get_input())
    strategy_name = strategy.get("type", ChunkStrategyType.tokens)
    strategy_config = {**strategy}
    strategy_exec = load_strategy(strategy_name)

    num_total = _get_num_total(output, column)
    tick = progress_ticker(callbacks.progress, num_total)

    output[to] = output.apply(
        cast(
            "Any",
            lambda x: run_strategy(strategy_exec, x[column], strategy_config, tick),
        ),
        axis=1,
    )
    return TableContainer(table=output)


def run_strategy(
    strategy: ChunkStrategy,
    input: ChunkInput,
    strategy_args: dict[str, Any],
    tick: ProgressTicker,
) -> list[str | tuple[list[str] | None, str, int]]:
    """
    执行strategy。

    Args:
        strategy (ChunkStrategy): strategy 参数。
        input (ChunkInput): input 参数。
        strategy_args (dict[str, Any]): strategy_args 参数。
        tick (ProgressTicker): tick 参数。

    Returns:
        处理结果。
    """
    if isinstance(input, str):
        return [item.text_chunk for item in strategy([input], {**strategy_args}, tick)]

    # We can work with both just a list of text content
    # or a list of tuples of (document_id, text content)
    # text_to_chunk = '''
    texts = []
    for item in input:
        if isinstance(item, str):
            texts.append(item)
        else:
            texts.append(item[1])

    strategy_results = strategy(texts, {**strategy_args}, tick)

    results = []
    for strategy_result in strategy_results:
        doc_indices = strategy_result.source_doc_indices
        if isinstance(input[doc_indices[0]], str):
            results.append(strategy_result.text_chunk)
        else:
            doc_ids = [input[doc_idx][0] for doc_idx in doc_indices]
            results.append(
                (
                    doc_ids,
                    strategy_result.text_chunk,
                    strategy_result.n_tokens,
                )
            )
    return results


def load_strategy(strategy: ChunkStrategyType) -> ChunkStrategy:
    """
    加载load_strategy。

    Args:
        strategy (ChunkStrategyType): strategy 参数。

    Returns:
        处理结果。
    """
    match strategy:
        case ChunkStrategyType.tokens:
            # from .strategies.tokens import run as run_tokens
            # return run_tokens

            from .strategies.doclist_tokens import run as run_doclist_tokens

            return run_doclist_tokens

        case ChunkStrategyType.sentence:
            # NLTK
            from ai.components.graphrag.index.bootstrap import bootstrap

            from .strategies.sentence import run as run_sentence

            bootstrap()
            return run_sentence
        case _:
            msg = f"Unknown strategy: {strategy}"
            raise ValueError(msg)
