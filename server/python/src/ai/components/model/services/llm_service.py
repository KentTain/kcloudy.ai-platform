"""
大语言模型服务

迁移自 Alon: src/alon/components/model/services/llm_service.py

提供所有 LLM 相关功能的统一接口，支持租户隔离和流式响应
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from typing import Any
from weakref import WeakValueDictionary

from ai.components.model.callbacks.base_callback import Callback
from ai.components.model.internal.model_instance_factory import (
    ModelInstance,
    ModelInstanceFactory,
)
from ai.components.model.services.base_model_service import BaseModelService
from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.entities.model.llm import LLMResult, LLMResultChunk
from ai_plugin.sdk.entities.model.message import PromptMessage, PromptMessageTool


class LLMService(BaseModelService):
    """
    大语言模型服务类

    封装所有 LLM 相关的操作，提供简洁易用的接口。
    支持单例模式，相同 tenant_id 返回相同实例。

    使用方式:
        service = LLMService(tenant_id="tenant-123")
        result = await service.invoke(prompt_messages=[...])
    """

    # 单例缓存：使用 WeakValueDictionary 避免内存泄漏
    # 当外部不再持有实例引用时，缓存会自动清理
    _instances: WeakValueDictionary[str, LLMService] = WeakValueDictionary()

    def __new__(cls, tenant_id: str) -> LLMService:
        """
        实现单例模式：相同 tenant_id 返回相同实例

        :param tenant_id: 租户 ID
        :return: LLMService 实例
        """
        if tenant_id in cls._instances:
            return cls._instances[tenant_id]

        instance = super().__new__(cls)
        cls._instances[tenant_id] = instance
        return instance

    def __init__(self, tenant_id: str):
        """
        初始化 LLM 服务

        由于单例模式，__init__ 可能被多次调用，
        需要检查是否已初始化避免重复操作。

        :param tenant_id: 租户 ID
        """
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._factory = ModelInstanceFactory()
        self._tenant_id = tenant_id
        self._initialized = True

    async def invoke(
        self,
        prompt_messages: Sequence[PromptMessage],
        model: str | None = None,
        provider: str | None = None,
        model_parameters: dict[str, Any] | None = None,
        tools: Sequence[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        user: str | None = None,
        callbacks: list[Callback] | None = None,
    ) -> LLMResult:
        """
        非流式 LLM 调用

        :param prompt_messages: 提示消息列表
        :param model: 模型名称（可选，不指定则使用默认模型）
        :param provider: 供应商名称（可选，不指定则使用默认供应商）
        :param model_parameters: 模型参数
        :param tools: 工具调用
        :param stop: 停止词
        :param user: 用户 ID
        :param callbacks: 回调函数列表
        :return: LLM 调用结果
        :raises ValueError: 未配置默认供应商
        :raises Exception: 模型返回结果类型错误
        """
        if not provider or not model:
            provider, model = await self._resolve_default_model(ModelType.LLM)

        model_instance: ModelInstance = await self._factory.get_model_instance(
            self._tenant_id,
            provider,
            model_type=ModelType.LLM,
            model=model,
        )

        result = model_instance.invoke_llm(
            prompt_messages=prompt_messages,
            model_parameters=model_parameters,
            tools=tools,
            stop=stop,
            stream=False,
            user=user,
            callbacks=callbacks,
        )

        async for chunk in result:
            if isinstance(chunk, LLMResult):
                return chunk

        raise Exception("模型结果不是 LLMResult")

    async def stream(
        self,
        prompt_messages: Sequence[PromptMessage],
        model: str | None = None,
        provider: str | None = None,
        model_parameters: dict[str, Any] | None = None,
        tools: Sequence[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        user: str | None = None,
        callbacks: list[Callback] | None = None,
    ) -> AsyncGenerator[LLMResultChunk, None]:
        """
        流式 LLM 调用

        :param prompt_messages: 提示消息列表
        :param model: 模型名称（可选，不指定则使用默认模型）
        :param provider: 供应商名称（可选，不指定则使用默认供应商）
        :param model_parameters: 模型参数
        :param tools: 工具调用
        :param stop: 停止词
        :param user: 用户 ID
        :param callbacks: 回调函数列表
        :return: 异步生成器，流式返回 LLMResultChunk
        :raises ValueError: 未配置默认供应商
        """
        if not provider or not model:
            provider, model = await self._resolve_default_model(ModelType.LLM)

        model_instance: ModelInstance = await self._factory.get_model_instance(
            self._tenant_id,
            provider,
            model_type=ModelType.LLM,
            model=model,
        )

        async for chunk in model_instance.invoke_llm(
            prompt_messages=prompt_messages,
            model_parameters=model_parameters,
            tools=tools,
            stop=stop,
            stream=True,
            user=user,
            callbacks=callbacks,
        ):
            if isinstance(chunk, LLMResultChunk):
                yield chunk

    async def tokens(
        self,
        prompt_messages: Sequence[PromptMessage],
        model: str | None = None,
        provider: str | None = None,
        tools: Sequence[PromptMessageTool] | None = None,
    ) -> int:
        """
        计算 token 数量

        :param prompt_messages: 提示消息列表
        :param model: 模型名称（可选，不指定则使用默认模型）
        :param provider: 供应商名称（可选，不指定则使用默认供应商）
        :param tools: 工具调用
        :return: token 数量
        :raises ValueError: 未配置默认供应商
        """
        if not provider or not model:
            provider, model = await self._resolve_default_model(ModelType.LLM)

        model_instance: ModelInstance = await self._factory.get_model_instance(
            self._tenant_id,
            provider,
            model_type=ModelType.LLM,
            model=model,
        )

        return await model_instance.get_llm_num_tokens(prompt_messages, tools)

    @classmethod
    def clear_instance(cls, tenant_id: str) -> None:
        """
        清除指定租户的单例实例

        :param tenant_id: 租户 ID
        """
        if tenant_id in cls._instances:
            del cls._instances[tenant_id]

    @classmethod
    def clear_all_instances(cls) -> None:
        """
        清除所有单例实例
        """
        cls._instances.clear()
