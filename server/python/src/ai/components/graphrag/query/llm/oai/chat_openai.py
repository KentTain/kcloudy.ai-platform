"""基于聊天的 OpenAI LLM 实现。

Chat-based OpenAI LLM implementation.
"""

from collections.abc import Callable
from typing import Any

from tenacity import (
    AsyncRetrying,
    RetryError,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ai.components.graphrag.query.llm.base import BaseLLM, BaseLLMCallback
from ai.components.graphrag.query.llm.oai.base import OpenAILLMImpl
from ai.components.graphrag.query.llm.oai.typing import (
    OPENAI_RETRY_ERROR_TYPES,
    OpenaiApiType,
)
from ai.components.graphrag.query.progress import StatusReporter

_MODEL_REQUIRED_MSG = "model is required"


class ChatOpenAI(BaseLLM, OpenAILLMImpl):
    """
    OpenAI ChatCompletion 模型的封装器。

    Wrapper for OpenAI ChatCompletion models.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        azure_ad_token_provider: Callable | None = None,
        deployment_name: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        api_type: OpenaiApiType = OpenaiApiType.OpenAI,
        organization: str | None = None,
        max_retries: int = 10,
        request_timeout: float = 180.0,
        retry_error_types: tuple[type[BaseException]] = OPENAI_RETRY_ERROR_TYPES,  # type: ignore
        reporter: StatusReporter | None = None,
    ):
        """
        初始化实例。

        Args:
            api_key (str | None): api_key 参数。
            model (str | None): model 参数。
            azure_ad_token_provider (Callable | None): azure_ad_token_provider 参数。
            deployment_name (str | None): deployment_name 参数。
            api_base (str | None): api_base 参数。
            api_version (str | None): api_version 参数。
            api_type (OpenaiApiType): api_type 参数。
            organization (str | None): organization 参数。
            max_retries (int): max_retries 参数。
            request_timeout (float): request_timeout 参数。
            retry_error_types (tuple[type[BaseException]]): retry_error_types 参数。
            reporter (StatusReporter | None): reporter 参数。
        """
        OpenAILLMImpl.__init__(
            self=self,
            api_key=api_key,
            azure_ad_token_provider=azure_ad_token_provider,
            deployment_name=deployment_name,
            api_base=api_base,
            api_version=api_version,
            api_type=api_type,  # type: ignore
            organization=organization,
            max_retries=max_retries,
            request_timeout=request_timeout,
            reporter=reporter,
        )
        self.model = model
        self.retry_error_types = retry_error_types

    def generate(
        self,
        messages: str | list[Any],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        生成文本。

        Generate text.

        参数 Parameters
        ----------
        - messages (str | list[Any]): 输入消息。Input messages
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
        except RetryError as e:
            self._reporter.error(
                message="Error at generate()", details={self.__class__.__name__: str(e)}
            )
            return ""
        else:
            # TODO: 为什么不在这种情况下抛出异常? / why not just throw in this case?
            return ""

    async def agenerate(
        self,
        messages: str | list[Any],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        异步生成文本。

        Generate text asynchronously.

        参数 Parameters
        ----------
        - messages (str | list[Any]): 输入消息。Input messages
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
                retry=retry_if_exception_type(self.retry_error_types),  # type: ignore
            )
            async for attempt in retryer:
                with attempt:
                    return await self._agenerate(
                        messages=messages,
                        streaming=streaming,
                        callbacks=callbacks,
                        **kwargs,
                    )
        except RetryError as e:
            self._reporter.error(f"Error at agenerate(): {e}")
            return ""
        else:
            # TODO: 为什么不在这种情况下抛出异常? / why not just throw in this case?
            return ""

    def _generate(
        self,
        messages: str | list[Any],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        生成generate。

        Args:
            messages (str | list[Any]): messages 参数。
            streaming (bool): streaming 参数。
            callbacks (list[BaseLLMCallback] | None): callbacks 参数。
            kwargs (Any): kwargs 参数。

        Returns:
            处理结果。
        """
        model = self.model
        if not model:
            raise ValueError(_MODEL_REQUIRED_MSG)
        # 调用 OpenAI API / Call OpenAI API
        response = self.sync_client.chat.completions.create(  # type: ignore
            model=model,
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
        messages: str | list[Any],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        处理agenerate。

        Args:
            messages (str | list[Any]): messages 参数。
            streaming (bool): streaming 参数。
            callbacks (list[BaseLLMCallback] | None): callbacks 参数。
            kwargs (Any): kwargs 参数。

        Returns:
            处理结果。
        """
        model = self.model
        if not model:
            raise ValueError(_MODEL_REQUIRED_MSG)
        # 异步调用 OpenAI API / Call OpenAI API asynchronously
        response = await self.async_client.chat.completions.create(  # type: ignore
            model=model,
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
