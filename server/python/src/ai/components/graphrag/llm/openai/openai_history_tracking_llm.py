"""历史记录跟踪 LLM 装饰器模块。

本模块提供一个 LLM 装饰器,用于自动跟踪和维护对话历史记录。
每次调用后会将用户输入和助手响应添加到历史记录中,支持多轮对话。
"""

from typing import Unpack

from ai.components.graphrag.llm.types import (
    LLM,
    CompletionInput,
    CompletionLLM,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)


class OpenAIHistoryTrackingLLM(LLM[CompletionInput, CompletionOutput]):
    """
    OpenAI 历史记录跟踪 LLM 装饰器。

    这个装饰器自动维护对话历史记录,在每次调用后更新历史,
    使得后续调用可以访问完整的对话上下文。
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
        history = kwargs.get("history") or []
        output = await self._delegate(input, **kwargs)
        return LLMOutput(
            output=output.output,
            json=output.json,
            history=[
                *history,
                {"role": "user", "content": input},
                {"role": "assistant", "content": output.output},
            ],
        )
