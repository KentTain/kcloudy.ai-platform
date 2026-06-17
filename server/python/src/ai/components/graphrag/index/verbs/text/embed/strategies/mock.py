"""包含 run and _embed_text methods definitions."""

import random
from collections.abc import Iterable
from typing import Any

from datashaper import ProgressTicker, VerbCallbacks, progress_ticker

from ai.components.graphrag.index.cache import PipelineCache
from ai.components.graphrag.index.verbs.text.embed.strategies.typing import (
    TextEmbeddingResult,
)


async def run(
    input: list[str],
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    _args: dict[str, Any],
) -> TextEmbeddingResult:
    """
    执行run。

    Args:
        input (list[str]): input 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        cache (PipelineCache): cache 参数。
        _args (dict[str, Any]): _args 参数。

    Returns:
        处理结果。
    """
    input = input if isinstance(input, Iterable) else [input]
    ticker = progress_ticker(callbacks.progress, len(input))
    return TextEmbeddingResult(
        embeddings=[_embed_text(cache, text, ticker) for text in input]
    )


def _embed_text(_cache: PipelineCache, _text: str, tick: ProgressTicker) -> list[float]:
    """
    嵌入embed_text。

    Args:
        _cache (PipelineCache): _cache 参数。
        _text (str): _text 参数。
        tick (ProgressTicker): tick 参数。

    Returns:
        处理结果。
    """
    tick(1)
    return [random.random(), random.random(), random.random()]
