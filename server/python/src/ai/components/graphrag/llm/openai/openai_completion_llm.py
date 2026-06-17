"""基于文本补全的语言模型实现模块。

本模块实现了基于 OpenAI Completions API (非聊天模式) 的语言模型。
这种模式适用于传统的文本补全任务,不涉及对话历史。

注意:OpenAI 新模型主要使用 Chat Completions API,此模块用于兼容旧模型。
"""

import logging
from typing import Unpack

from ai.components.graphrag.llm.base import BaseLLM
from ai.components.graphrag.llm.openai.openai_configuration import OpenAIConfiguration
from ai.components.graphrag.llm.openai.types import OpenAIClientTypes
from ai.components.graphrag.llm.openai.utils import get_completion_llm_args
from ai.components.graphrag.llm.types import (
    CompletionInput,
    CompletionOutput,
    LLMInput,
)

log = logging.getLogger(__name__)


class OpenAICompletionLLM(BaseLLM[CompletionInput, CompletionOutput]):
    """
    基于文本补全的 LLM 实现。

    使用 OpenAI 的 Completions API 实现的语言模型,用于简单的文本补全任务。
    不支持对话历史,适用于单次补全场景。
    """

    _client: OpenAIClientTypes
    _configuration: OpenAIConfiguration

    def __init__(self, client: OpenAIClientTypes, configuration: OpenAIConfiguration):
        """
        初始化实例。

        Args:
            client (OpenAIClientTypes): client 参数。
            configuration (OpenAIConfiguration): configuration 参数。
        """
        self.client = client
        self.configuration = configuration

    async def _execute_llm(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> CompletionOutput | None:
        """
        执行execute_llm。

        Args:
            input (CompletionInput): input 参数。
            kwargs (Unpack[LLMInput]): kwargs 参数。

        Returns:
            处理结果。
        """
        args = get_completion_llm_args(
            kwargs.get("model_parameters"), self.configuration
        )
        completion = self.client.completions.create(prompt=input, **args)
        return completion.choices[0].text
