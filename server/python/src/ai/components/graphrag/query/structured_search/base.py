"""搜索算法的基类。

Base classes for search algos.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd
import tiktoken

from ai.components.graphrag.query.context_builder.builders import (
    GlobalContextBuilder,
    LocalContextBuilder,
)
from ai.components.graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from ai.components.graphrag.query.llm.base import BaseLLM


@dataclass
class SearchResult:
    """
    结构化搜索结果。

    A Structured Search Result.
    """

    response: str | dict[str, Any] | list[dict[str, Any]]
    context_data: str | list[pd.DataFrame] | dict[str, pd.DataFrame]
    # 上下文窗口中的实际文本字符串,由 context_data 构建 / actual text strings that are in the context window, built from context_data
    context_text: str | list[str] | dict[str, str]
    completion_time: float
    llm_calls: int
    prompt_tokens: int


class BaseSearch(ABC):
    """
    搜索的基类实现。

    The Base Search implementation.
    """

    def __init__(
        self,
        llm: BaseLLM,
        context_builder: GlobalContextBuilder | LocalContextBuilder,
        token_encoder: tiktoken.Encoding | None = None,
        llm_params: dict[str, Any] | None = None,
        context_builder_params: dict[str, Any] | None = None,
    ):
        """
        初始化实例。

        Args:
            llm (BaseLLM): llm 参数。
            context_builder (GlobalContextBuilder | LocalContextBuilder): context_builder 参数。
            token_encoder (tiktoken.Encoding | None): token_encoder 参数。
            llm_params (dict[str, Any] | None): llm_params 参数。
            context_builder_params (dict[str, Any] | None): context_builder_params 参数。
        """
        self.llm = llm
        self.context_builder = context_builder
        self.token_encoder = token_encoder
        self.llm_params = llm_params or {}
        self.context_builder_params = context_builder_params or {}

    @abstractmethod
    def search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> SearchResult:
        """
        搜索给定的查询。

        Search for the given query.
        """

    @abstractmethod
    async def asearch(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> SearchResult:
        """
        异步搜索给定的查询。

        Search for the given query asynchronously.
        """
