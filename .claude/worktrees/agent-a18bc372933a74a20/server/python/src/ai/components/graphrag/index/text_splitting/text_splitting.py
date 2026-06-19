"""包含 'Tokenizer','TextSplitter','NoopTextSplitter' 和 'TokenTextSplitter' 模型的模块."""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, cast

import pandas as pd
import tiktoken

from ai.components.graphrag.index.utils import num_tokens_from_string

EncodedText = list[int]
DecodeFn = Callable[[EncodedText], str]
EncodeFn = Callable[[str], EncodedText]
LengthFn = Callable[[str], int]

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Tokenizer:
    """分词器数据类."""

    chunk_overlap: int
    """块之间的 token 重叠数"""
    tokens_per_chunk: int
    """每个块的最大 token 数"""
    decode: DecodeFn
    """将 token id 列表解码为字符串的函数"""
    encode: EncodeFn
    """将字符串编码为 token id 列表的函数"""


class TextSplitter(ABC):
    """文本分割器类定义."""

    _chunk_size: int
    _chunk_overlap: int
    _length_function: LengthFn
    _keep_separator: bool
    _add_start_index: bool
    _strip_whitespace: bool

    def __init__(
        self,
        # 基于 text-ada-002-embedding 最大输入缓冲区长度
        # https://platform.openai.com/docs/guides/embeddings/second-generation-models
        chunk_size: int = 8191,
        chunk_overlap: int = 100,
        length_function: LengthFn = len,
        keep_separator: bool = False,
        add_start_index: bool = False,
        strip_whitespace: bool = True,
    ):
        """初始化方法定义."""
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._length_function = length_function
        self._keep_separator = keep_separator
        self._add_start_index = add_start_index
        self._strip_whitespace = strip_whitespace

    @abstractmethod
    def split_text(self, text: str | list[str]) -> Iterable[str]:
        """分割文本方法定义."""


class NoopTextSplitter(TextSplitter):
    """无操作文本分割器类定义."""

    def split_text(self, text: str | list[str]) -> Iterable[str]:
        """分割文本方法定义."""
        return [text] if isinstance(text, str) else text


class TokenTextSplitter(TextSplitter):
    """Token 文本分割器类定义."""

    _allowed_special: Literal["all"] | set[str]
    _disallowed_special: Literal["all"] | Collection[str]

    def __init__(
        self,
        encoding_name: str = "cl100k_base",
        model_name: str | None = None,
        allowed_special: Literal["all"] | set[str] | None = None,
        disallowed_special: Literal["all"] | Collection[str] = "all",
        **kwargs: Any,
    ):
        """初始化方法定义."""
        super().__init__(**kwargs)
        if model_name is not None:
            try:
                enc = tiktoken.encoding_for_model(model_name)
            except KeyError:
                log.exception("Model %s not found, using %s", model_name, encoding_name)
                enc = tiktoken.get_encoding(encoding_name)
        else:
            enc = tiktoken.get_encoding(encoding_name)
        self._tokenizer = enc
        self._allowed_special = allowed_special or set()
        self._disallowed_special = disallowed_special

    def encode(self, text: str) -> list[int]:
        """将给定文本编码为整数向量."""
        return self._tokenizer.encode(
            text,
            allowed_special=self._allowed_special,
            disallowed_special=self._disallowed_special,
        )

    def num_tokens(self, text: str) -> int:
        """返回字符串中的 token 数."""
        return len(self.encode(text))

    def split_text(self, text: str | list[str]) -> list[str]:
        """分割文本方法."""
        if cast("bool", pd.isna(text)) or text == "":
            return []
        if isinstance(text, list):
            text = " ".join(text)
        if not isinstance(text, str):
            msg = f"Attempting to split a non-string value, actual is {type(text)}"
            raise TypeError(msg)

        tokenizer = Tokenizer(
            chunk_overlap=self._chunk_overlap,
            tokens_per_chunk=self._chunk_size,
            decode=self._tokenizer.decode,
            encode=lambda text: self.encode(text),
        )

        return split_text_on_tokens(text=text, tokenizer=tokenizer)


class TextListSplitterType(str, Enum):
    """TextListSplitter 类型的枚举."""

    DELIMITED_STRING = "delimited_string"
    JSON = "json"


class TextListSplitter(TextSplitter):
    """文本列表分割器类定义."""

    def __init__(
        self,
        chunk_size: int,
        splitter_type: TextListSplitterType = TextListSplitterType.JSON,
        input_delimiter: str | None = None,
        output_delimiter: str | None = None,
        model_name: str | None = None,
        encoding_name: str | None = None,
    ):
        """使用块大小初始化 TextListSplitter."""
        # 将块重叠设置为 0,因为我们使用完整字符串
        super().__init__(chunk_size, chunk_overlap=0)
        self._type = splitter_type
        self._input_delimiter = input_delimiter
        self._output_delimiter = output_delimiter or "\n"
        self._length_function = lambda x: num_tokens_from_string(
            x, model=model_name, encoding_name=encoding_name
        )

    def split_text(self, text: str | list[str]) -> Iterable[str]:
        """将字符串列表分割为给定块大小的字符串列表."""
        if not text:
            return []

        result: list[str] = []
        current_chunk: list[str] = []

        # 添加括号
        current_length: int = self._length_function("[]")

        # 输入应该是由分隔符连接的字符串列表
        string_list = self._load_text_list(text)

        if len(string_list) == 1:
            return string_list

        for item in string_list:
            # 计算项的长度并添加逗号
            item_length = self._length_function(f"{item},")

            if current_length + item_length > self._chunk_size:
                if current_chunk and len(current_chunk) > 0:
                    # 将当前块添加到结果中
                    self._append_to_result(result, current_chunk)

                    # 开始新的块
                    current_chunk = [item]
                    # 为括号添加 2
                    current_length = item_length
            else:
                # 将项添加到当前块
                current_chunk.append(item)
                # 为逗号添加 1
                current_length += item_length

        # 将最后一个块添加到结果中
        self._append_to_result(result, current_chunk)

        return result

    def _load_text_list(self, text: str | list[str]):
        """根据类型加载文本列表."""
        if isinstance(text, list):
            string_list = text
        elif self._type == TextListSplitterType.JSON:
            string_list = json.loads(text)
        else:
            string_list = text.split(self._input_delimiter)
        return string_list

    def _append_to_result(self, chunk_list: list[str], new_chunk: list[str]):
        """将当前块添加到结果中."""
        if new_chunk and len(new_chunk) > 0:
            if self._type == TextListSplitterType.JSON:
                chunk_list.append(json.dumps(new_chunk, ensure_ascii=False))
            else:
                chunk_list.append(self._output_delimiter.join(new_chunk))


def split_text_on_tokens(*, text: str, tokenizer: Tokenizer) -> list[str]:
    """使用分词器分割传入的文本并返回块."""
    splits: list[str] = []
    input_ids = tokenizer.encode(text)
    start_idx = 0
    cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
    chunk_ids = input_ids[start_idx:cur_idx]
    while start_idx < len(input_ids):
        splits.append(tokenizer.decode(chunk_ids))
        start_idx += tokenizer.tokens_per_chunk - tokenizer.chunk_overlap
        cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
        chunk_ids = input_ids[start_idx:cur_idx]
    return splits
