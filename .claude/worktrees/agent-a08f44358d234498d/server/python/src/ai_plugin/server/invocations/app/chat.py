from collections.abc import Generator
from typing import Literal, overload

from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class ChatAppInvocation(BackwardsInvocation[dict]):
    """聊天应用调用类

    用于调用聊天类型的应用，支持流式和阻塞两种响应模式，支持对话上下文管理。
    """

    @overload
    def invoke(
        self,
        app_id: str,
        query: str,
        inputs: dict,
        response_mode: Literal["streaming"],
        conversation_id: str | None = None,
    ) -> Generator[dict, None, None]: ...

    @overload
    def invoke(
        self,
        app_id: str,
        query: str,
        inputs: dict,
        response_mode: Literal["blocking"],
        conversation_id: str | None = None,
    ) -> dict: ...

    def invoke(
        self,
        app_id: str,
        query: str,
        inputs: dict,
        response_mode: Literal["streaming", "blocking"] = "streaming",
        conversation_id: str | None = None,
    ) -> Generator[dict, None, None] | dict:
        """调用聊天应用

        Args:
            app_id: 应用ID
            query: 用户查询内容
            inputs: 输入参数字典
            response_mode: 响应模式，支持"streaming"(流式)和"blocking"(阻塞)，默认为流式
            conversation_id: 对话ID，用于维持对话上下文，可选

        Returns:
            根据响应模式返回生成器或字典结果

        Raises:
            Exception: 当聊天应用没有响应时抛出异常
        """
        response = self._backwards_invoke(
            InvokeType.App,
            dict,
            {
                "app_id": app_id,
                "query": query,
                "inputs": inputs,
                "response_mode": response_mode,
                "conversation_id": conversation_id,
            },
        )

        # 如果是流式模式，直接返回生成器
        if response_mode == "streaming":
            return response

        # 阻塞模式下，返回第一个响应数据
        for data in response:
            return data

        raise Exception("聊天应用没有响应")
