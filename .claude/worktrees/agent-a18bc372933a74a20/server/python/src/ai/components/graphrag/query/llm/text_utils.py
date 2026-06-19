"""LLM 的文本工具函数。

Text Utilities for LLM.
"""

from collections.abc import Iterator
from itertools import islice

import tiktoken


def num_tokens(text: str, token_encoder: tiktoken.Encoding | None = None) -> int:
    """
    返回给定文本中的令牌数量。

    Return the number of tokens in the given text.

    参数 Parameters
    ----------
    - text (str): 要计算令牌数的文本。Text to count tokens
    - token_encoder (tiktoken.Encoding | None): 令牌编码器,默认使用 cl100k_base。Token encoder, defaults to cl100k_base

    返回 Returns
    -------
    - int: 令牌数量。Number of tokens
    """
    if token_encoder is None:
        token_encoder = tiktoken.get_encoding("cl100k_base")
    return len(token_encoder.encode(text))  # type: ignore


def batched(iterable: Iterator, n: int):
    """
    将数据批处理为长度为 n 的元组。最后一批可能更短。

    Batch data into tuples of length n. The last batch may be shorter.

    取自 Python 的 cookbook:https://docs.python.org/3/library/itertools.html#itertools.batched
    Taken from Python's cookbook: https://docs.python.org/3/library/itertools.html#itertools.batched

    参数 Parameters
    ----------
    - iterable (Iterator): 可迭代对象。Iterable object
    - n (int): 每批的大小。Size of each batch

    生成 Yields
    ------
    - tuple: 批处理的元组。Batched tuples

    示例 Example
    --------
    batched('ABCDEFG', 3) --> ABC DEF G
    """
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        value_error = "n must be at least one"
        raise ValueError(value_error)
    it = iter(iterable)
    # 使用海象运算符批量获取数据 / Use walrus operator to batch data
    while batch := tuple(islice(it, n)):
        yield batch


def chunk_text(
    text: str, max_tokens: int, token_encoder: tiktoken.Encoding | None = None
):
    """
    按令牌长度分块文本。

    Chunk text by token length.

    参数 Parameters
    ----------
    - text (str): 要分块的文本。Text to chunk
    - max_tokens (int): 每块的最大令牌数。Maximum tokens per chunk
    - token_encoder (tiktoken.Encoding | None): 令牌编码器,默认使用 cl100k_base。Token encoder, defaults to cl100k_base

    生成 Yields
    ------
    - str: 分块后的文本。Chunked text
    """
    if token_encoder is None:
        token_encoder = tiktoken.get_encoding("cl100k_base")
    # 将文本编码为令牌 / Encode text to tokens
    tokens = token_encoder.encode(text)  # type: ignore
    # 批处理令牌 / Batch tokens
    chunk_iterator = batched(iter(tokens), max_tokens)
    # 解码每个批次并生成 / Decode each batch and yield
    yield from (token_encoder.decode(list(chunk)) for chunk in chunk_iterator)
