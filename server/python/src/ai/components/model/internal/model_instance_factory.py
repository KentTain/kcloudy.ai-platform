"""
模型实例工厂

迁移自 Alon: src/alon/components/model/internal/model_instance_factory.py

负责创建和管理模型实例，提供统一的模型调用接口
"""

from collections.abc import AsyncGenerator, Sequence
from typing import cast

from loguru import logger

from ai.components.model.errors.error import ProviderTokenNotInitError
from ai.components.model.internal.provider_configuration import ProviderModelBundle
from ai.components.model.internal.provider_manager import ProviderManager
from ai.components.model.model_providers.__base__.large_language_model import (
    LargeLanguageModelImpl,
)
from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.entities.model.llm import LLMResult, LLMResultChunk
from ai_plugin.sdk.entities.model.message import PromptMessage, PromptMessageTool

_logger = logger.bind(name=__name__)


class ModelInstance:
    """
    模型实例类

    封装具体的模型实例，提供统一的调用接口
    """

    def __init__(self, provider_model_bundle: ProviderModelBundle, model: str) -> None:
        """
        初始化模型实例

        :param provider_model_bundle: 供应商模型束
        :param model: 模型名称
        """
        self.provider_model_bundle = provider_model_bundle
        self.model = model
        self.provider = provider_model_bundle.configuration.provider.provider
        self.credentials = self._fetch_credentials_from_bundle(
            provider_model_bundle, model
        )
        self.model_type_instance = self.provider_model_bundle.model_type_instance

    @staticmethod
    def _fetch_credentials_from_bundle(
        provider_model_bundle: ProviderModelBundle, model: str
    ) -> dict:
        """
        从供应商模型束中获取凭证信息

        :param provider_model_bundle: 供应商模型束
        :param model: 模型名称
        :return: 凭证字典
        """
        configuration = provider_model_bundle.configuration
        model_type = provider_model_bundle.model_type_instance.model_type
        credentials = configuration.get_current_credentials(
            model_type=model_type, model=model
        )

        if credentials is None:
            raise ProviderTokenNotInitError(f"模型 {model} 的凭证未初始化。")

        return credentials

    async def invoke_llm(
        self,
        prompt_messages: Sequence[PromptMessage],
        model_parameters: dict | None = None,
        tools: Sequence[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> AsyncGenerator[LLMResult | LLMResultChunk, None]:
        """
        调用大语言模型

        :param prompt_messages: 提示消息
        :param model_parameters: 模型参数
        :param tools: 工具调用
        :param stop: 停止词
        :param stream: 是否流式响应
        :param user: 唯一用户 ID
        :return: 异步生成器，流式返回 LLMResultChunk，非流式返回 LLMResult
        """
        if not isinstance(self.model_type_instance, LargeLanguageModelImpl):
            raise Exception("模型类型实例不是 LargeLanguageModel")

        self.model_type_instance = cast(
            LargeLanguageModelImpl, self.model_type_instance
        )

        result = await self._async_round_robin_invoke(
            function=self.model_type_instance.invoke,
            model=self.model,
            credentials=self.credentials,
            prompt_messages=list(prompt_messages),
            model_parameters=model_parameters,
            tools=list(tools) if tools else None,
            stop=list(stop) if stop else None,
            stream=stream,
            user=user,
        )

        # 如果结果是 AsyncGenerator，直接 yield 每个 chunk
        if stream and isinstance(result, AsyncGenerator):
            async for chunk in result:
                yield chunk
        elif isinstance(result, LLMResult):
            # 对于非流式结果，也通过生成器 yield 一次完整结果
            yield result
        else:
            raise Exception("模型结果不是 LLMResult 或 AsyncGenerator")

    async def get_llm_num_tokens(
        self,
        prompt_messages: Sequence[PromptMessage],
        tools: Sequence[PromptMessageTool] | None = None,
    ) -> int:
        """
        获取大语言模型的 token 数量

        :param prompt_messages: 提示消息
        :param tools: 工具调用
        :return: token 数量
        """
        if not isinstance(self.model_type_instance, LargeLanguageModelImpl):
            raise Exception("模型类型实例不是 LargeLanguageModel")

        self.model_type_instance = cast(
            LargeLanguageModelImpl, self.model_type_instance
        )
        return cast(
            int,
            await self._async_round_robin_invoke(
                function=self.model_type_instance.get_num_tokens,
                model=self.model,
                credentials=self.credentials,
                prompt_messages=list(prompt_messages),
                tools=list(tools) if tools else None,
            ),
        )

    async def _round_robin_invoke(self, function, **kwargs):
        """
        轮询调用函数
        """
        return function(**kwargs)

    async def _async_round_robin_invoke(self, function, **kwargs):
        """
        异步轮询调用函数
        """
        import asyncio

        if asyncio.iscoroutinefunction(function):
            return await function(**kwargs)
        else:
            return function(**kwargs)


class ModelInstanceFactory:
    """
    模型实例工厂

    负责管理和创建模型实例
    """

    def __init__(self) -> None:
        """初始化模型实例工厂"""
        self._provider_manager = ProviderManager()

    async def get_model_instance(
        self,
        tenant_id: str,
        provider: str,
        model_type: ModelType,
        model: str,
    ) -> ModelInstance:
        """
        获取模型实例

        :param tenant_id: 租户 ID
        :param provider: 供应商名称
        :param model_type: 模型类型
        :param model: 模型名称
        :return: 模型实例
        """
        provider_model_bundle = await self._provider_manager._get_provider_model_bundle(
            tenant_id=tenant_id,
            provider=provider,
            model_type=model_type,
        )

        return ModelInstance(provider_model_bundle, model)

    async def get_default_provider_model_name(
        self,
        tenant_id: str,
        model_type: ModelType,
    ) -> tuple[str | None, str | None]:
        """
        获取默认的供应商和模型名称

        :param tenant_id: 租户 ID
        :param model_type: 模型类型
        :return: (供应商名称, 模型名称) 元组
        """
        return await self._provider_manager.get_default_provider_model_name(
            tenant_id=tenant_id, model_type=model_type
        )

    async def get_default_model_instance(
        self, tenant_id: str, model_type: ModelType
    ) -> ModelInstance:
        """
        获取默认模型实例

        :param tenant_id: 租户 ID
        :param model_type: 模型类型
        :return: 默认模型实例
        """
        provider, model = await self.get_default_provider_model_name(
            tenant_id, model_type
        )
        if not provider or not model:
            raise ValueError(f"没有为 {model_type.value} 类型配置默认模型")

        return await self.get_model_instance(tenant_id, provider, model_type, model)
