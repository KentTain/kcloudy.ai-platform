"""OpenAI Embedding 模型实现。

OpenAI Embedding model implementation.
"""

import asyncio
from collections.abc import Callable
from typing import Any

import numpy as np
import tiktoken
from tenacity import (
    AsyncRetrying,
    RetryError,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ai.components.graphrag.query.llm.base import BaseTextEmbedding
from ai.components.graphrag.query.llm.oai.base import OpenAILLMImpl
from ai.components.graphrag.query.llm.oai.typing import (
    OPENAI_RETRY_ERROR_TYPES,
    OpenaiApiType,
)
from ai.components.graphrag.query.llm.text_utils import chunk_text
from ai.components.graphrag.query.progress import StatusReporter


class OpenAIEmbedding(BaseTextEmbedding, OpenAILLMImpl):
    """
    OpenAI Embedding 模型的封装器。

    Wrapper for OpenAI Embedding models.
    """

    def __init__(
        self,
        api_key: str | None = None,
        azure_ad_token_provider: Callable | None = None,
        model: str = "text-embedding-3-small",
        deployment_name: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        api_type: OpenaiApiType = OpenaiApiType.OpenAI,
        organization: str | None = None,
        encoding_name: str = "cl100k_base",
        max_tokens: int = 8191,
        max_retries: int = 10,
        request_timeout: float = 180.0,
        retry_error_types: tuple[type[BaseException]] = OPENAI_RETRY_ERROR_TYPES,  # type: ignore
        reporter: StatusReporter | None = None,
    ):
        """
        初始化实例。

        Args:
            api_key (str | None): api_key 参数。
            azure_ad_token_provider (Callable | None): azure_ad_token_provider 参数。
            model (str): model 参数。
            deployment_name (str | None): deployment_name 参数。
            api_base (str | None): api_base 参数。
            api_version (str | None): api_version 参数。
            api_type (OpenaiApiType): api_type 参数。
            organization (str | None): organization 参数。
            encoding_name (str): encoding_name 参数。
            max_tokens (int): max_tokens 参数。
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
        self.encoding_name = encoding_name
        self.max_tokens = max_tokens
        self.token_encoder = tiktoken.get_encoding(self.encoding_name)
        self.retry_error_types = retry_error_types

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """
        使用 OpenAI Embedding 的同步函数嵌入文本。

        Embed text using OpenAI Embedding's sync function.

        对于长度超过 max_tokens 的文本,将文本分块为 max_tokens,嵌入每个块,然后使用加权平均组合。
        For text longer than max_tokens, chunk texts into max_tokens, embed each chunk, then combine using weighted average.

        参考:https://github.com/openai/openai-cookbook/blob/main/examples/Embedding_long_inputs.ipynb
        Please refer to: https://github.com/openai/openai-cookbook/blob/main/examples/Embedding_long_inputs.ipynb

        参数 Parameters
        ----------
        - text (str): 要嵌入的文本。Text to embed
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - list[float]: 嵌入向量。Embedding vector
        """
        # 将文本分块 / Chunk text
        token_chunks = chunk_text(
            text=text, token_encoder=self.token_encoder, max_tokens=self.max_tokens
        )
        chunk_embeddings = []
        chunk_lens = []
        for chunk in token_chunks:
            try:
                embedding, chunk_len = self._embed_with_retry(chunk, **kwargs)
                chunk_embeddings.append(embedding)
                chunk_lens.append(chunk_len)
            # TODO: 捕获更具体的异常 / catch a more specific exception
            except Exception as e:
                self._reporter.error(
                    message="Error embedding chunk",
                    details={self.__class__.__name__: str(e)},
                )

                continue
        # 使用加权平均组合块嵌入 / Combine chunk embeddings using weighted average
        chunk_embeddings = np.average(chunk_embeddings, axis=0, weights=chunk_lens)
        # 归一化嵌入向量 / Normalize embedding vector
        chunk_embeddings = chunk_embeddings / np.linalg.norm(chunk_embeddings)
        return chunk_embeddings.tolist()

    async def aembed(self, text: str, **kwargs: Any) -> list[float]:
        """
        使用 OpenAI Embedding 的异步函数嵌入文本。

        Embed text using OpenAI Embedding's async function.

        对于长度超过 max_tokens 的文本,将文本分块为 max_tokens,嵌入每个块,然后使用加权平均组合。
        For text longer than max_tokens, chunk texts into max_tokens, embed each chunk, then combine using weighted average.

        参数 Parameters
        ----------
        - text (str): 要嵌入的文本。Text to embed
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - list[float]: 嵌入向量。Embedding vector
        """
        # 将文本分块 / Chunk text
        token_chunks = chunk_text(
            text=text, token_encoder=self.token_encoder, max_tokens=self.max_tokens
        )
        chunk_embeddings = []
        chunk_lens = []
        # 并行处理所有块 / Process all chunks in parallel
        embedding_results = await asyncio.gather(
            *[self._aembed_with_retry(chunk, **kwargs) for chunk in token_chunks]
        )
        # 过滤有效结果 / Filter valid results
        embedding_results = [result for result in embedding_results if result[0]]
        chunk_embeddings = [result[0] for result in embedding_results]
        chunk_lens = [result[1] for result in embedding_results]
        # 使用加权平均组合块嵌入 / Combine chunk embeddings using weighted average
        chunk_embeddings = np.average(chunk_embeddings, axis=0, weights=chunk_lens)  # type: ignore
        # 归一化嵌入向量 / Normalize embedding vector
        chunk_embeddings = chunk_embeddings / np.linalg.norm(chunk_embeddings)
        return chunk_embeddings.tolist()

    def _embed_with_retry(
        self, text: str | tuple, **kwargs: Any
    ) -> tuple[list[float], int]:
        """
        带重试的嵌入函数。

        Embedding function with retry.

        参数 Parameters
        ----------
        - text (str | tuple): 要嵌入的文本。Text to embed
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - tuple[list[float], int]: (嵌入向量, 文本长度)。(Embedding vector, text length)
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
                    # 调用 OpenAI Embeddings API / Call OpenAI Embeddings API
                    embedding = (
                        self.sync_client.embeddings.create(  # type: ignore
                            input=text,
                            model=self.model,
                            **kwargs,  # type: ignore
                        )
                        .data[0]
                        .embedding
                        or []
                    )
                    return (embedding, len(text))
        except RetryError as e:
            self._reporter.error(
                message="Error at embed_with_retry()",
                details={self.__class__.__name__: str(e)},
            )
            return ([], 0)
        else:
            # TODO: 为什么不在这种情况下抛出异常? / why not just throw in this case?
            return ([], 0)

    async def _aembed_with_retry(
        self, text: str | tuple, **kwargs: Any
    ) -> tuple[list[float], int]:
        """
        带重试的异步嵌入函数。

        Asynchronous embedding function with retry.

        参数 Parameters
        ----------
        - text (str | tuple): 要嵌入的文本。Text to embed
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - tuple[list[float], int]: (嵌入向量, 文本长度)。(Embedding vector, text length)
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
                    # 异步调用 OpenAI Embeddings API / Call OpenAI Embeddings API asynchronously
                    embedding = (
                        await self.async_client.embeddings.create(  # type: ignore
                            input=text,
                            model=self.model,
                            **kwargs,  # type: ignore
                        )
                    ).data[0].embedding or []
                    return (embedding, len(text))
        except RetryError as e:
            self._reporter.error(
                message="Error at embed_with_retry()",
                details={self.__class__.__name__: str(e)},
            )
            return ([], 0)
        else:
            # TODO: 为什么不在这种情况下抛出异常? / why not just throw in this case?
            return ([], 0)
