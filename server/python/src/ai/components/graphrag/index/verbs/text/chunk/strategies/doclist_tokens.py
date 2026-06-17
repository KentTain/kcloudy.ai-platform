"""包含 run 方法定义的模块."""

import json
from collections.abc import Iterable
from typing import Any

from datashaper import ProgressTicker

from ai.components.graphrag.index.verbs.text.chunk.strategies.tokens import (
    run as run_tokens,
)
from ai.components.graphrag.index.verbs.text.chunk.strategies.typing import TextChunk
from ai.components.graphrag.webserver.utils.consts import DOC_TYPE_DOC_LIST


def run(
    input: list[str], args: dict[str, Any], tick: ProgressTicker
) -> Iterable[TextChunk]:
    """
    执行run。

    Args:
        input (list[str]): input 参数。
        args (dict[str, Any]): args 参数。
        tick (ProgressTicker): tick 参数。

    Yields:
        迭代产生的结果。
    """
    for doc_idx, text in enumerate(input):
        # print(f"doclist_tokens Chunking text doc_idx:{doc_idx},  {text}")
        if text.startswith(DOC_TYPE_DOC_LIST):
            print(f"doclist_tokens Chunking text doc_idx:{doc_idx}")
            text = text[len(DOC_TYPE_DOC_LIST) :]

            list = json.loads(text)
            for doc in list:
                yield TextChunk(
                    text_chunk=doc,
                    source_doc_indices=[doc_idx],
                    n_tokens=len(doc),
                )
            tick(1)
        else:
            print(f"run_tokens Chunking text doc_idx:{doc_idx}")
            # 回归到tokens的方式
            chunks = run_tokens(input=[text], args=args, tick=tick)

            yield from chunks
