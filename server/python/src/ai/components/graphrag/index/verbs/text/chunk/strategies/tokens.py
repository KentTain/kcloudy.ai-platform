"""包含 run and split_text_on_tokens methods definition."""

from collections.abc import Iterable
from typing import Any

import tiktoken
from datashaper import ProgressTicker

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.index.text_splitting import Tokenizer
from ai.components.graphrag.index.verbs.text.chunk.typing import TextChunk


def run(
    input: list[str], args: dict[str, Any], tick: ProgressTicker
) -> Iterable[TextChunk]:
    """
    执行run。

    Args:
        input (list[str]): input 参数。
        args (dict[str, Any]): args 参数。
        tick (ProgressTicker): tick 参数。

    Returns:
        处理结果。
    """
    tokens_per_chunk = args.get("chunk_size", defs.CHUNK_SIZE)
    chunk_overlap = args.get("chunk_overlap", defs.CHUNK_OVERLAP)
    encoding_name = args.get("encoding_name", defs.ENCODING_MODEL)
    enc = tiktoken.get_encoding(encoding_name)

    def encode(text: str) -> list[int]:
        """
        编码encode。

        Args:
            text (str): text 参数。

        Returns:
            处理结果。
        """
        if not isinstance(text, str):
            text = f"{text}"
        return enc.encode(text)

    def decode(tokens: list[int]) -> str:
        """
        解码decode。

        Args:
            tokens (list[int]): tokens 参数。

        Returns:
            处理结果。
        """
        return enc.decode(tokens)

    return split_text_on_tokens(
        input,
        Tokenizer(
            chunk_overlap=chunk_overlap,
            tokens_per_chunk=tokens_per_chunk,
            encode=encode,
            decode=decode,
        ),
        tick,
    )


# Adapted from - https://github.com/langchain-ai/langchain/blob/77b359edf5df0d37ef0d539f678cf64f5557cb54/libs/langchain/langchain/text_splitter.py#L471
# So we could have better control over the chunking process
def split_text_on_tokens(
    texts: list[str], enc: Tokenizer, tick: ProgressTicker
) -> list[TextChunk]:
    """
    拆分split_text_on_tokens。

    Args:
        texts (list[str]): texts 参数。
        enc (Tokenizer): enc 参数。
        tick (ProgressTicker): tick 参数。

    Returns:
        处理结果。
    """
    result = []
    mapped_ids = []

    for source_doc_idx, text in enumerate(texts):
        encoded = enc.encode(text)
        tick(1)
        mapped_ids.append((source_doc_idx, encoded))

    input_ids: list[tuple[int, int]] = [
        (source_doc_idx, id) for source_doc_idx, ids in mapped_ids for id in ids
    ]

    start_idx = 0
    cur_idx = min(start_idx + enc.tokens_per_chunk, len(input_ids))
    chunk_ids = input_ids[start_idx:cur_idx]
    while start_idx < len(input_ids):
        chunk_text = enc.decode([id for _, id in chunk_ids])
        doc_indices = list({doc_idx for doc_idx, _ in chunk_ids})
        result.append(
            TextChunk(
                text_chunk=chunk_text,
                source_doc_indices=doc_indices,
                n_tokens=len(chunk_ids),
            )
        )
        start_idx += enc.tokens_per_chunk - enc.chunk_overlap
        cur_idx = min(start_idx + enc.tokens_per_chunk, len(input_ids))
        chunk_ids = input_ids[start_idx:cur_idx]

    return result
