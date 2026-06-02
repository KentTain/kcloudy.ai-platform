from collections.abc import Generator
from typing import Literal, overload

from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class CompletionAppInvocation(BackwardsInvocation[dict]):
    """文本补全应用调用类

    用于调用文本补全类型的应用，支持流式和阻塞两种响应模式。
    """

    @overload
    def invoke(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["streaming"],
    ) -> Generator[dict, None, None]: ...

    @overload
    def invoke(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["blocking"],
    ) -> dict: ...

    def invoke(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["streaming", "blocking"] = "blocking",
    ) -> Generator[dict, None, None] | dict:
        """调用文本补全应用

        Args:
            app_id: 应用ID
            inputs: 输入参数字典
            response_mode: 响应模式，支持"streaming"(流式)和"blocking"(阻塞)

        Returns:
            根据响应模式返回生成器或字典结果

        Raises:
            Exception: 当补全应用没有响应时抛出异常
        """
        response = self._backwards_invoke(
            InvokeType.App,
            dict,
            {
                "app_id": app_id,
                "inputs": inputs,
                "response_mode": response_mode,
            },
        )

        # 如果是流式模式，直接返回生成器
        if response_mode == "streaming":
            return response

        # 阻塞模式下，返回第一个响应数据
        for data in response:
            return data

        raise Exception("文本补全应用没有响应")
