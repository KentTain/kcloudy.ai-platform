"""
基础 LLM 类定义

定义了所有 LLM 实现的基础抽象类。
"""

import traceback
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Unpack

from ai.components.graphrag.llm.types import (
    LLM,
    ErrorHandlerFn,
    LLMInput,
    LLMOutput,
)

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class BaseLLM(ABC, LLM[TIn, TOut], Generic[TIn, TOut]):
    """
    LLM 实现的基础抽象类

    提供了 LLM 调用的基础框架,包括错误处理和 JSON 输出支持。
    所有具体的 LLM 实现都应该继承此类。
    """

    _on_error: ErrorHandlerFn | None

    def on_error(self, on_error: ErrorHandlerFn | None) -> None:
        """
        设置错误处理函数

        Args:
            on_error: 错误处理函数,当 LLM 调用失败时调用
        """
        self._on_error = on_error

    @abstractmethod
    async def _execute_llm(
        self,
        input: TIn,
        **kwargs: Unpack[LLMInput],
    ) -> TOut | None:
        """
        执行 LLM 调用的抽象方法

        子类必须实现此方法来定义具体的 LLM 调用逻辑。

        Args:
            input: 输入数据
            **kwargs: 额外的 LLM 输入参数

        Returns
        -------
            LLM 的输出结果
        """

    async def __call__(
        self,
        input: TIn,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[TOut]:
        """
        调用 LLM

        根据参数决定是普通调用还是 JSON 模式调用。

        Args:
            input: 输入数据
            **kwargs: 额外的 LLM 输入参数

        Returns
        -------
            LLM 输出结果的包装对象
        """
        is_json = kwargs.get("json") or False
        if is_json:
            return await self._invoke_json(input, **kwargs)
        return await self._invoke(input, **kwargs)

    async def _invoke(self, input: TIn, **kwargs: Unpack[LLMInput]) -> LLMOutput[TOut]:
        """
        执行普通的 LLM 调用

        Args:
            input: 输入数据
            **kwargs: 额外的 LLM 输入参数

        Returns
        -------
            LLM 输出结果的包装对象

        Raises
        ------
            Exception: 如果 LLM 调用失败,会调用错误处理函数后重新抛出异常
        """
        try:
            output = await self._execute_llm(input, **kwargs)
            return LLMOutput(output=output)
        except Exception as e:
            stack_trace = traceback.format_exc()
            if self._on_error:
                self._on_error(e, stack_trace, {"input": input})
            raise

    async def _invoke_json(
        self, input: TIn, **kwargs: Unpack[LLMInput]
    ) -> LLMOutput[TOut]:
        """
        执行 JSON 模式的 LLM 调用

        默认实现不支持 JSON 输出,子类需要重写此方法来提供 JSON 输出支持。

        Args:
            input: 输入数据
            **kwargs: 额外的 LLM 输入参数

        Returns
        -------
            LLM 输出结果的包装对象

        Raises
        ------
            NotImplementedError: 当前 LLM 不支持 JSON 输出
        """
        msg = "JSON output not supported by this LLM"
        raise NotImplementedError(msg)
