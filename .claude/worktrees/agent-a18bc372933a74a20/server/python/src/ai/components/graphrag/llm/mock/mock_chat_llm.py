"""
模拟聊天 LLM

提供了一个返回预设响应序列的 Mock ChatLLM 实现,主要用于测试。
"""

from typing import Unpack

from ai.components.graphrag.llm.base import BaseLLM
from ai.components.graphrag.llm.types import (
    CompletionInput,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)


class MockChatLLM(
    BaseLLM[
        CompletionInput,
        CompletionOutput,
    ]
):
    """
    模拟聊天 LLM

    按顺序返回预设的响应列表,每次调用返回下一个响应。
    主要用于单元测试和集成测试。
    """

    responses: list[str]
    i: int = 0

    def __init__(self, responses: list[str]):
        """
        初始化模拟聊天 LLM

        Args:
            responses: 预设的响应列表,按调用顺序返回
        """
        self.i = 0
        self.responses = responses

    def _create_output(
        self,
        output: CompletionOutput | None,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[CompletionOutput]:
        """
        创建 LLM 输出对象

        Args:
            output: 输出内容
            **kwargs: 额外参数,包括历史记录

        Returns
        -------
            包含输出和更新后历史记录的 LLMOutput 对象
        """
        history = kwargs.get("history") or []
        return LLMOutput[CompletionOutput](
            output=output, history=[*history, {"content": output}]
        )

    async def _execute_llm(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> CompletionOutput:
        """
        执行 LLM 调用,返回下一个预设响应

        Args:
            input: 输入内容(会被忽略)
            **kwargs: 额外参数

        Returns
        -------
            当前索引对应的响应字符串

        Raises
        ------
            ValueError: 如果响应列表已用尽
        """
        if self.i >= len(self.responses):
            msg = f"No more responses, requested {self.i} but only have {len(self.responses)}"
            raise ValueError(msg)
        response = self.responses[self.i]
        self.i += 1
        return response
