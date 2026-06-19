"""LLM 和嵌入模型的基类。

Base classes for LLM and Embedding models.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

from openai import AsyncAzureOpenAI, AsyncOpenAI, AzureOpenAI, OpenAI

from ai.components.graphrag.query.llm.base import BaseTextEmbedding
from ai.components.graphrag.query.llm.oai.typing import OpenaiApiType
from ai.components.graphrag.query.progress import (
    ConsoleStatusReporter,
    StatusReporter,
)


class BaseOpenAILLM(ABC):
    """
    OpenAI LLM 基类实现。

    The Base OpenAI LLM implementation.
    """

    _async_client: AsyncOpenAI | AsyncAzureOpenAI
    _sync_client: OpenAI | AzureOpenAI

    def __init__(self):
        """初始化实例。"""
        self._create_openai_client()

    @abstractmethod
    def _create_openai_client(self):
        """
        创建新的同步和异步 OpenAI 客户端实例。

        Create a new synchronous and asynchronous OpenAI client instance.
        """

    def set_clients(
        self,
        sync_client: OpenAI | AzureOpenAI,
        async_client: AsyncOpenAI | AsyncAzureOpenAI,
    ):
        """
        设置用于发送 API 请求的同步和异步客户端。

        Set the synchronous and asynchronous clients used for making API requests.

        参数 Args
        ----
        - sync_client (OpenAI | AzureOpenAI): 同步客户端对象。The sync client object.
        - async_client (AsyncOpenAI | AsyncAzureOpenAI): 异步客户端对象。The async client object.
        """
        self._sync_client = sync_client
        self._async_client = async_client

    @property
    def async_client(self) -> AsyncOpenAI | AsyncAzureOpenAI | None:
        """
        获取用于发送 API 请求的异步客户端。

        Get the asynchronous client used for making API requests.

        返回 Returns
        -------
        - AsyncOpenAI | AsyncAzureOpenAI: 异步客户端对象。The async client object.
        """
        return self._async_client

    @property
    def sync_client(self) -> OpenAI | AzureOpenAI | None:
        """
        获取用于发送 API 请求的同步客户端。

        Get the synchronous client used for making API requests.

        返回 Returns
        -------
        - AsyncOpenAI | AsyncAzureOpenAI: 异步客户端对象。The async client object.
        """
        return self._sync_client

    @async_client.setter
    def async_client(self, client: AsyncOpenAI | AsyncAzureOpenAI):
        """
        设置用于发送 API 请求的异步客户端。

        Set the asynchronous client used for making API requests.

        参数 Args
        ----
        - client (AsyncOpenAI | AsyncAzureOpenAI): 异步客户端对象。The async client object.
        """
        self._async_client = client

    @sync_client.setter
    def sync_client(self, client: OpenAI | AzureOpenAI):
        """
        设置用于发送 API 请求的同步客户端。

        Set the synchronous client used for making API requests.

        参数 Args
        ----
        - client (OpenAI | AzureOpenAI): 同步客户端对象。The sync client object.
        """
        self._sync_client = client


class OpenAILLMImpl(BaseOpenAILLM):
    """
    编排 OpenAI LLM 实现。

    Orchestration OpenAI LLM Implementation.
    """

    _reporter: StatusReporter = ConsoleStatusReporter()

    def __init__(
        self,
        api_key: str | None = None,
        azure_ad_token_provider: Callable | None = None,
        deployment_name: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        api_type: OpenaiApiType = OpenaiApiType.OpenAI,
        organization: str | None = None,
        max_retries: int = 10,
        request_timeout: float = 180.0,
        reporter: StatusReporter | None = None,
    ):
        """
        初始化实例。

        Args:
            api_key (str | None): api_key 参数。
            azure_ad_token_provider (Callable | None): azure_ad_token_provider 参数。
            deployment_name (str | None): deployment_name 参数。
            api_base (str | None): api_base 参数。
            api_version (str | None): api_version 参数。
            api_type (OpenaiApiType): api_type 参数。
            organization (str | None): organization 参数。
            max_retries (int): max_retries 参数。
            request_timeout (float): request_timeout 参数。
            reporter (StatusReporter | None): reporter 参数。
        """
        self.api_key = api_key
        self.azure_ad_token_provider = azure_ad_token_provider
        self.deployment_name = deployment_name
        self.api_base = api_base
        self.api_version = api_version
        self.api_type = api_type
        self.organization = organization
        self.max_retries = max_retries
        self.request_timeout = request_timeout
        self.reporter = reporter or ConsoleStatusReporter()

        try:
            # 创建 OpenAI 同步和异步客户端 / Create OpenAI sync and async clients
            super().__init__()
        except Exception as e:
            self._reporter.error(
                message="Failed to create OpenAI client",
                details={self.__class__.__name__: str(e)},
            )
            raise

    def _create_openai_client(self):
        """
        创建新的 OpenAI 客户端实例。

        Create a new OpenAI client instance.
        """
        if self.api_type == OpenaiApiType.AzureOpenAI:
            if self.api_base is None:
                msg = "api_base is required for Azure OpenAI"
                raise ValueError(msg)

            # 创建 Azure OpenAI 同步客户端 / Create Azure OpenAI sync client
            sync_client = AzureOpenAI(
                api_key=self.api_key,
                azure_ad_token_provider=self.azure_ad_token_provider,
                organization=self.organization,
                # Azure 特定配置 / Azure-Specifics
                api_version=self.api_version,
                azure_endpoint=self.api_base,
                azure_deployment=self.deployment_name,
                # 重试配置 / Retry Configuration
                timeout=self.request_timeout,
                max_retries=self.max_retries,
            )

            # 创建 Azure OpenAI 异步客户端 / Create Azure OpenAI async client
            async_client = AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_ad_token_provider=self.azure_ad_token_provider,
                organization=self.organization,
                # Azure 特定配置 / Azure-Specifics
                api_version=self.api_version,
                azure_endpoint=self.api_base,
                azure_deployment=self.deployment_name,
                # 重试配置 / Retry Configuration
                timeout=self.request_timeout,
                max_retries=self.max_retries,
            )
            self.set_clients(sync_client=sync_client, async_client=async_client)

        else:
            # 创建标准 OpenAI 同步客户端 / Create standard OpenAI sync client
            sync_client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                organization=self.organization,
                # 重试配置 / Retry Configuration
                timeout=self.request_timeout,
                max_retries=self.max_retries,
            )

            # 创建标准 OpenAI 异步客户端 / Create standard OpenAI async client
            async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                organization=self.organization,
                # 重试配置 / Retry Configuration
                timeout=self.request_timeout,
                max_retries=self.max_retries,
            )
            self.set_clients(sync_client=sync_client, async_client=async_client)


class OpenAITextEmbeddingImpl(BaseTextEmbedding):
    """
    编排 OpenAI 文本嵌入实现。

    Orchestration OpenAI Text Embedding Implementation.
    """

    _reporter: StatusReporter | None = None

    def _create_openai_client(self, api_type: OpenaiApiType):
        """
        创建新的同步和异步 OpenAI 客户端实例。

        Create a new synchronous and asynchronous OpenAI client instance.
        """
