"""包含 run 方法定义的模块."""

from collections.abc import Iterable
from typing import Any

import nltk
from datashaper import ProgressTicker

from ai.components.graphrag.index.verbs.text.chunk.strategies.typing import TextChunk


def run(
    input: list[str], _args: dict[str, Any], tick: ProgressTicker
) -> Iterable[TextChunk]:
    """
    执行run。

    Args:
        input (list[str]): input 参数。
        _args (dict[str, Any]): _args 参数。
        tick (ProgressTicker): tick 参数。

    Yields:
        迭代产生的结果。
    """
    for doc_idx, text in enumerate(input):
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            yield TextChunk(
                text_chunk=sentence,
                source_doc_indices=[doc_idx],
            )
        tick(1)
