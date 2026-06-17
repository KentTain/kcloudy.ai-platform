"""基于先前提问的问题和最新上下文数据生成问题的基类。

Base classes for generating questions based on previously asked questions and most recent context data.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import tiktoken

from ai.components.graphrag.query.context_builder.builders import (
    GlobalContextBuilder,
    LocalContextBuilder,
)
from ai.components.graphrag.query.llm.base import BaseLLM


@dataclass
class QuestionResult:
    """
    结构化问题结果。

    A Structured Question Result.
    """

    response: list[str]
    context_data: str | dict[str, Any]
    completion_time: float
    llm_calls: int
    prompt_tokens: int


class BaseQuestionGen(ABC):
    """
    问题生成的基类实现。

    The Base Question Gen implementation.
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
    def generate(
        self,
        question_history: list[str],
        context_data: str | None,
        question_count: int,
        **kwargs,
    ) -> QuestionResult:
        """
        生成问题。

        Generate questions.
        """

    @abstractmethod
    async def agenerate(
        self,
        question_history: list[str],
        context_data: str | None,
        question_count: int,
        **kwargs,
    ) -> QuestionResult:
        """
        异步生成问题。

        Generate questions asynchronously.
        """
