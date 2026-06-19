"""
LLM 协议定义

定义了 LLM 的基础协议接口。
"""

from typing import Generic, Protocol, TypeVar, Unpack

from ai.components.graphrag.llm.types.llm_io import (
    LLMInput,
    LLMOutput,
)

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class LLM(Protocol, Generic[TIn, TOut]):
    """
    LLM 协议定义

    所有 LLM 实现都应该遵循此协议,提供统一的调用接口。
    """

    async def __call__(
        self,
        input: TIn,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[TOut]:
        """
        调用 LLM,将 LLM 作为函数使用

        Args:
            input: 输入数据
            **kwargs: 额外的 LLM 输入参数

        Returns
        -------
            LLM 输出结果的包装对象
        """
        ...
