"""变量替换 LLM 装饰器模块。

本模块提供一个 LLM 装饰器,用于在调用前自动替换输入和历史记录中的变量占位符。
支持使用 {variable_name} 语法在提示词中插入动态变量值。
"""

from typing import Unpack

from ai.components.graphrag.llm.openai.utils import perform_variable_replacements
from ai.components.graphrag.llm.types import (
    LLM,
    CompletionInput,
    CompletionLLM,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)


class OpenAITokenReplacingLLM(LLM[CompletionInput, CompletionOutput]):
    """
    OpenAI 变量替换 LLM 装饰器。

    这个装饰器在调用底层 LLM 之前,自动替换输入文本和历史记录中的
    变量占位符。占位符使用 {variable_name} 格式,会被替换为实际的变量值。
    """

    _delegate: CompletionLLM

    def __init__(self, delegate: CompletionLLM):
        """
        初始化实例。

        Args:
            delegate (CompletionLLM): delegate 参数。
        """
        self._delegate = delegate

    async def __call__(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[CompletionOutput]:
        """
        实现 __call__ 协议方法。

        Args:
            input (CompletionInput): input 参数。
            kwargs (Unpack[LLMInput]): kwargs 参数。

        Returns:
            处理结果。
        """
        variables = kwargs.get("variables")
        history = kwargs.get("history") or []
        # 执行变量替换
        input = perform_variable_replacements(input, history, variables)
        return await self._delegate(input, **kwargs)
