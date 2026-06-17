"""
模拟补全 LLM

提供了一个返回固定响应的 Mock CompletionLLM 实现,主要用于测试。
"""

import logging
from typing import Unpack

from ai.components.graphrag.llm.base import BaseLLM
from ai.components.graphrag.llm.types import (
    CompletionInput,
    CompletionOutput,
    LLMInput,
)

log = logging.getLogger(__name__)


class MockCompletionLLM(
    BaseLLM[
        CompletionInput,
        CompletionOutput,
    ]
):
    """
    模拟补全 LLM

    始终返回响应列表中的第一个响应,主要用于测试。
    与 MockChatLLM 不同,此类不会递增索引,每次都返回相同的响应。
    """

    def __init__(self, responses: list[str]):
        """
        初始化模拟补全 LLM

        Args:
            responses: 预设的响应列表,只使用第一个元素
        """
        self.responses = responses
        self._on_error = None

    async def _execute_llm(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> CompletionOutput:
        """
        执行 LLM 调用,始终返回第一个预设响应

        Args:
            input: 输入内容(会被忽略)
            **kwargs: 额外参数

        Returns
        -------
            响应列表中的第一个响应字符串
        """
        return self.responses[0]
