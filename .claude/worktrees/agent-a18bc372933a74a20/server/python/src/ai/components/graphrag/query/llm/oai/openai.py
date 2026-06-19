"""编排的 OpenAI 封装器。

OpenAI Wrappers for Orchestration.
"""

import logging
from typing import Any

from tenacity import (
    AsyncRetrying,
    RetryError,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ai.components.graphrag.query.llm.base import BaseLLMCallback
from ai.components.graphrag.query.llm.oai.base import OpenAILLMImpl
from ai.components.graphrag.query.llm.oai.typing import (
    OPENAI_RETRY_ERROR_TYPES,
    OpenaiApiType,
)

log = logging.getLogger(__name__)


class OpenAI(OpenAILLMImpl):
    """
    OpenAI Completion 模型的封装器。

    Wrapper for OpenAI Completion models.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        deployment_name: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        api_type: OpenaiApiType = OpenaiApiType.OpenAI,
        organization: str | None = None,
        max_retries: int = 10,
        retry_error_types: tuple[type[BaseException]] = OPENAI_RETRY_ERROR_TYPES,  # type: ignore
    ):
        """
        初始化实例。

        Args:
            api_key (str): api_key 参数。
            model (str): model 参数。
            deployment_name (str | None): deployment_name 参数。
            api_base (str | None): api_base 参数。
            api_version (str | None): api_version 参数。
            api_type (OpenaiApiType): api_type 参数。
            organization (str | None): organization 参数。
            max_retries (int): max_retries 参数。
            retry_error_types (tuple[type[BaseException]]): retry_error_types 参数。
        """
        self.api_key = api_key
        self.model = model
        self.deployment_name = deployment_name
        self.api_base = api_base
        self.api_version = api_version
        self.api_type = api_type
        self.organization = organization
        self.max_retries = max_retries
        self.retry_error_types = retry_error_types

    def generate(
        self,
        messages: str | list[str],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        生成文本。

        Generate text.

        参数 Parameters
        ----------
        - messages (str | list[str]): 输入消息。Input messages
        - streaming (bool): 是否使用流式输出。Whether to use streaming
        - callbacks (list[BaseLLMCallback] | None): 回调列表。Callback list
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - str: 生成的文本。Generated text
        """
        try:
            # 创建重试器 / Create retryer
            retryer = Retrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential_jitter(max=10),
                reraise=True,
                retry=retry_if_exception_type(self.retry_error_types),
            )
            for attempt in retryer:
                with attempt:
                    return self._generate(
                        messages=messages,
                        streaming=streaming,
                        callbacks=callbacks,
                        **kwargs,
                    )
        except RetryError:
            log.exception("RetryError at generate(): %s")
            return ""
        else:
            # TODO: 为什么不在这种情况下抛出异常? / why not just throw in this case?
            return ""

    async def agenerate(
        self,
        messages: str | list[str],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        异步生成文本。

        Generate Text Asynchronously.

        参数 Parameters
        ----------
        - messages (str | list[str]): 输入消息。Input messages
        - streaming (bool): 是否使用流式输出。Whether to use streaming
        - callbacks (list[BaseLLMCallback] | None): 回调列表。Callback list
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - str: 生成的文本。Generated text
        """
        try:
            # 创建异步重试器 / Create async retryer
            retryer = AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential_jitter(max=10),
                reraise=True,
                retry=retry_if_exception_type(self.retry_error_types),
            )
            async for attempt in retryer:
                with attempt:
                    return await self._agenerate(
                        messages=messages,
                        streaming=streaming,
                        callbacks=callbacks,
                        **kwargs,
                    )
        except RetryError:
            log.exception("Error at agenerate()")
            return ""
        else:
            # TODO: 为什么不在这种情况下抛出异常? / why not just throw in this case?
            return ""

    def _generate(
        self,
        messages: str | list[str],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        # 调用 OpenAI Chat Completions API / Call OpenAI Chat Completions API
        """
        生成generate。

        Args:
            messages (str | list[str]): messages 参数。
            streaming (bool): streaming 参数。
            callbacks (list[BaseLLMCallback] | None): callbacks 参数。
            kwargs (Any): kwargs 参数。

        Returns:
            处理结果。
        """
        response = self.sync_client.chat.completions.create(  # type: ignore
            model=self.model,
            messages=messages,  # type: ignore
            stream=streaming,
            **kwargs,
        )  # type: ignore
        if streaming:
            # 处理流式响应 / Handle streaming response
            full_response = ""
            usage = None
            while True:
                try:
                    chunk = response.__next__()  # type: ignore
                    if not chunk or not chunk.choices:
                        continue

                    # 提取增量内容 / Extract delta content
                    delta = (
                        chunk.choices[0].delta.content
                        if chunk.choices[0].delta and chunk.choices[0].delta.content
                        else ""
                    )  # type: ignore

                    full_response += delta
                    # 调用回调函数 / Call callbacks
                    if callbacks:
                        for callback in callbacks:
                            callback.on_llm_new_token(delta)
                    # 检查是否停止 / Check if stopped
                    if chunk.choices[0].finish_reason == "stop":  # type: ignore
                        usage = chunk.usage
                        break
                except StopIteration:
                    break
            # 调用停止回调 / Call stop callbacks
            if callbacks:
                for callback in callbacks:
                    callback.on_llm_stop(usage=usage)
            return full_response
        return response.choices[0].message.content or ""  # type: ignore

    async def _agenerate(
        self,
        messages: str | list[str],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        # 异步调用 OpenAI Chat Completions API / Call OpenAI Chat Completions API asynchronously
        """
        处理agenerate。

        Args:
            messages (str | list[str]): messages 参数。
            streaming (bool): streaming 参数。
            callbacks (list[BaseLLMCallback] | None): callbacks 参数。
            kwargs (Any): kwargs 参数。

        Returns:
            处理结果。
        """
        response = await self.async_client.chat.completions.create(  # type: ignore
            model=self.model,
            messages=messages,  # type: ignore
            stream=streaming,
            **kwargs,
        )
        if streaming:
            # 处理异步流式响应 / Handle async streaming response
            full_response = ""
            usage = None
            while True:
                try:
                    chunk = await response.__anext__()  # type: ignore
                    if not chunk or not chunk.choices:
                        continue

                    # 提取增量内容 / Extract delta content
                    delta = (
                        chunk.choices[0].delta.content
                        if chunk.choices[0].delta and chunk.choices[0].delta.content
                        else ""
                    )  # type: ignore

                    full_response += delta
                    # 调用回调函数 / Call callbacks
                    if callbacks:
                        for callback in callbacks:
                            callback.on_llm_new_token(delta)
                    # 检查是否停止 / Check if stopped
                    if chunk.choices[0].finish_reason == "stop":  # type: ignore
                        usage = chunk.usage
                        break
                except StopIteration:
                    break
            # 调用停止回调 / Call stop callbacks
            if callbacks:
                for callback in callbacks:
                    callback.on_llm_stop(usage=usage)
            return full_response
        return response.choices[0].message.content or ""  # type: ignore
