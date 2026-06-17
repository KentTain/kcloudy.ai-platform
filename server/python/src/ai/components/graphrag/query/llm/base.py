"""LLM 和嵌入模型的基类。

Base classes for LLM and Embedding models.
"""

from abc import ABC, abstractmethod
from typing import Any

from openai.types import CompletionUsage


class BaseLLMCallback:
    """
    LLM 回调的基类。

    Base class for LLM callbacks.
    """

    def __init__(self):
        # 存储响应令牌 / Store response tokens
        """初始化实例。"""
        self.response = []

    def on_llm_new_token(self, token: str):
        """
        处理生成新令牌时的回调。

        Handle when a new token is generated.

        参数 Parameters
        ----------
        - token (str): 新生成的令牌。New generated token
        """
        self.response.append(token)

    def on_llm_stop(self, usage: CompletionUsage | None):
        """
        处理 LLM 停止生成时的回调。

        Handle when LLM stops generating.

        参数 Parameters
        ----------
        - usage (CompletionUsage | None): 使用情况统计。Usage statistics
        """


class BaseLLM(ABC):
    """
    LLM 基类实现。

    The Base LLM implementation.
    """

    @abstractmethod
    def generate(
        self,
        messages: str | list[Any],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        生成响应。

        Generate a response.

        参数 Parameters
        ----------
        - messages (str | list[Any]): 输入消息。Input messages
        - streaming (bool): 是否使用流式输出。Whether to use streaming output
        - callbacks (list[BaseLLMCallback] | None): 回调列表。Callback list
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - str: 生成的响应。Generated response
        """

    @abstractmethod
    async def agenerate(
        self,
        messages: str | list[Any],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        异步生成响应。

        Generate a response asynchronously.

        参数 Parameters
        ----------
        - messages (str | list[Any]): 输入消息。Input messages
        - streaming (bool): 是否使用流式输出。Whether to use streaming output
        - callbacks (list[BaseLLMCallback] | None): 回调列表。Callback list
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - str: 生成的响应。Generated response
        """


class BaseTextEmbedding(ABC):
    """
    文本嵌入接口。

    The text embedding interface.
    """

    @abstractmethod
    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """
        嵌入文本字符串。

        Embed a text string.

        参数 Parameters
        ----------
        - text (str): 要嵌入的文本。Text to embed
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - list[float]: 嵌入向量。Embedding vector
        """

    @abstractmethod
    async def aembed(self, text: str, **kwargs: Any) -> list[float]:
        """
        异步嵌入文本字符串。

        Embed a text string asynchronously.

        参数 Parameters
        ----------
        - text (str): 要嵌入的文本。Text to embed
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - list[float]: 嵌入向量。Embedding vector
        """
