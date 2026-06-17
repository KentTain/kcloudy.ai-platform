"""加载LLM工具."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import TYPE_CHECKING, Any

from ai.components.graphrag.config.enums import LLMType
from ai.components.graphrag.llm import (
    CompletionLLM,
    EmbeddingLLM,
    LLMCache,
    LLMLimiter,
    MockCompletionLLM,
    OpenAIConfiguration,
    create_openai_chat_llm,
    create_openai_client,
    create_openai_completion_llm,
    create_openai_embedding_llm,
    create_tpm_rpm_limiters,
)

if TYPE_CHECKING:
    from datashaper import VerbCallbacks

    from ai.components.graphrag.index.cache import PipelineCache
    from ai.components.graphrag.index.typing import ErrorHandlerFn

log = logging.getLogger(__name__)

_semaphores: dict[str, asyncio.Semaphore] = {}
_rate_limiters: dict[str, LLMLimiter] = {}


def _get_task_factory():
    """延迟导入 task_factory，避免启动时加载 webserver 模块."""
    from ai.components.graphrag.webserver.task.task import task_factory

    return task_factory


def load_llm(
    name: str,
    llm_type: LLMType,
    callbacks: VerbCallbacks,
    cache: PipelineCache | None,
    llm_config: dict[str, Any] | None = None,
    chat_only=False,
) -> CompletionLLM:
    """为实体提取链加载LLM."""
    on_error = _create_error_handler(callbacks)

    if llm_type in loaders:
        if chat_only and not loaders[llm_type]["chat"]:
            msg = f"LLM type {llm_type} does not support chat"
            raise ValueError(msg)
        if cache is not None:
            cache = cache.child(name)

        loader = loaders[llm_type]
        return loader["load"](on_error, cache, llm_config or {})

    msg = f"Unknown LLM type {llm_type}"
    raise ValueError(msg)


def load_llm_embeddings(
    name: str,
    llm_type: LLMType,
    callbacks: VerbCallbacks,
    cache: PipelineCache | None,
    llm_config: dict[str, Any] | None = None,
    chat_only=False,
) -> EmbeddingLLM:
    """为实体提取链加载LLM嵌入模型."""
    on_error = _create_error_handler(callbacks)
    if llm_type in loaders:
        if chat_only and not loaders[llm_type]["chat"]:
            msg = f"LLM type {llm_type} does not support chat"
            raise ValueError(msg)
        if cache is not None:
            cache = cache.child(name)

        return loaders[llm_type]["load"](on_error, cache, llm_config or {})

    msg = f"Unknown LLM type {llm_type}"
    raise ValueError(msg)


def _create_error_handler(callbacks: VerbCallbacks) -> ErrorHandlerFn:
    """
    创建error_handler。

    Args:
        callbacks (VerbCallbacks): callbacks 参数。

    Returns:
        处理结果。
    """

    def on_error(
        error: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        """
        处理on_error。

        Args:
            error (BaseException | None): error 参数。
            stack (str | None): stack 参数。
            details (dict | None): details 参数。
        """
        callbacks.error("Error Invoking LLM", error, stack, details)

    return on_error


def _load_openai_completion_llm(
    on_error: ErrorHandlerFn,
    cache: LLMCache,
    config: dict[str, Any],
    azure=False,
):
    """
    加载load_openai_completion_llm。

    Args:
        on_error (ErrorHandlerFn): on_error 参数。
        cache (LLMCache): cache 参数。
        config (dict[str, Any]): config 参数。
        azure: azure 参数。

    Returns:
        处理结果。
    """
    return _create_openai_completion_llm(
        OpenAIConfiguration(
            {
                **_get_base_config(config),
                "model": config.get("model", "gpt-4-turbo-preview"),
                "deployment_name": config.get("deployment_name"),
                "temperature": config.get("temperature", 0.0),
                "frequency_penalty": config.get("frequency_penalty", 0),
                "presence_penalty": config.get("presence_penalty", 0),
                "top_p": config.get("top_p", 1),
                "max_tokens": config.get("max_tokens", 4000),
                "n": config.get("n"),
            }
        ),
        on_error,
        cache,
        azure,
    )


def _load_openai_chat_llm(
    on_error: ErrorHandlerFn,
    cache: LLMCache,
    config: dict[str, Any],
    azure=False,
):
    """
    加载load_openai_chat_llm。

    Args:
        on_error (ErrorHandlerFn): on_error 参数。
        cache (LLMCache): cache 参数。
        config (dict[str, Any]): config 参数。
        azure: azure 参数。

    Returns:
        处理结果。
    """
    return _create_openai_chat_llm(
        OpenAIConfiguration(
            {
                # 设置默认值
                **_get_base_config(config),
                "model": config.get("model", "gpt-4-turbo-preview"),
                "deployment_name": config.get("deployment_name"),
                "temperature": config.get("temperature", 0.0),
                "frequency_penalty": config.get("frequency_penalty", 0),
                "presence_penalty": config.get("presence_penalty", 0),
                "top_p": config.get("top_p", 1),
                "max_tokens": config.get("max_tokens"),
                "n": config.get("n"),
            }
        ),
        on_error,
        cache,
        azure,
    )


def _load_openai_embeddings_llm(
    on_error: ErrorHandlerFn,
    cache: LLMCache,
    config: dict[str, Any],
    azure=False,
):
    """
    加载load_openai_embeddings_llm。

    Args:
        on_error (ErrorHandlerFn): on_error 参数。
        cache (LLMCache): cache 参数。
        config (dict[str, Any]): config 参数。
        azure: azure 参数。

    Returns:
        处理结果。
    """
    return _create_openai_embeddings_llm(
        OpenAIConfiguration(
            {
                **_get_base_config(config),
                "model": config.get(
                    "embeddings_model", config.get("model", "text-embedding-3-small")
                ),
                "deployment_name": config.get("deployment_name"),
            }
        ),
        on_error,
        cache,
        azure,
    )


def _load_azure_openai_completion_llm(
    on_error: ErrorHandlerFn, cache: LLMCache, config: dict[str, Any]
):
    """
    加载load_azure_openai_completion_llm。

    Args:
        on_error (ErrorHandlerFn): on_error 参数。
        cache (LLMCache): cache 参数。
        config (dict[str, Any]): config 参数。

    Returns:
        处理结果。
    """
    return _load_openai_completion_llm(on_error, cache, config, True)


def _load_azure_openai_chat_llm(
    on_error: ErrorHandlerFn, cache: LLMCache, config: dict[str, Any]
):
    """
    加载load_azure_openai_chat_llm。

    Args:
        on_error (ErrorHandlerFn): on_error 参数。
        cache (LLMCache): cache 参数。
        config (dict[str, Any]): config 参数。

    Returns:
        处理结果。
    """
    return _load_openai_chat_llm(on_error, cache, config, True)


def _load_azure_openai_embeddings_llm(
    on_error: ErrorHandlerFn, cache: LLMCache, config: dict[str, Any]
):
    """
    加载load_azure_openai_embeddings_llm。

    Args:
        on_error (ErrorHandlerFn): on_error 参数。
        cache (LLMCache): cache 参数。
        config (dict[str, Any]): config 参数。

    Returns:
        处理结果。
    """
    return _load_openai_embeddings_llm(on_error, cache, config, True)


def _get_base_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    获取base_config。

    Args:
        config (dict[str, Any]): config 参数。

    Returns:
        处理结果。
    """
    api_key = config.get("api_key")

    return {
        # 传入所有参数化的值
        **config,
        # 设置默认值
        "api_key": api_key,
        "api_base": config.get("api_base"),
        "api_version": config.get("api_version"),
        "organization": config.get("organization"),
        "proxy": config.get("proxy"),
        "max_retries": config.get("max_retries", 10),
        "request_timeout": config.get("request_timeout", 60.0),
        "model_supports_json": config.get("model_supports_json"),
        "concurrent_requests": config.get("concurrent_requests", 4),
        "encoding_model": config.get("encoding_model", "cl100k_base"),
        "cognitive_services_endpoint": config.get("cognitive_services_endpoint"),
    }


def _load_static_response(
    _on_error: ErrorHandlerFn, _cache: PipelineCache, config: dict[str, Any]
) -> CompletionLLM:
    """
    加载load_static_response。

    Args:
        _on_error (ErrorHandlerFn): _on_error 参数。
        _cache (PipelineCache): _cache 参数。
        config (dict[str, Any]): config 参数。

    Returns:
        处理结果。
    """
    return MockCompletionLLM(config.get("responses", []))


loaders = {
    LLMType.OpenAI: {
        "load": _load_openai_completion_llm,
        "chat": False,
    },
    LLMType.AzureOpenAI: {
        "load": _load_azure_openai_completion_llm,
        "chat": False,
    },
    LLMType.OpenAIChat: {
        "load": _load_openai_chat_llm,
        "chat": True,
    },
    LLMType.AzureOpenAIChat: {
        "load": _load_azure_openai_chat_llm,
        "chat": True,
    },
    LLMType.OpenAIEmbedding: {
        "load": _load_openai_embeddings_llm,
        "chat": False,
    },
    LLMType.AzureOpenAIEmbedding: {
        "load": _load_azure_openai_embeddings_llm,
        "chat": False,
    },
    LLMType.StaticResponse: {
        "load": _load_static_response,
        "chat": False,
    },
}


def _create_openai_chat_llm(
    configuration: OpenAIConfiguration,
    on_error: ErrorHandlerFn,
    cache: LLMCache,
    azure=False,
) -> CompletionLLM:
    """创建OpenAI聊天LLM."""
    client = create_openai_client(configuration=configuration, azure=azure)
    limiter = _create_limiter(configuration)
    semaphore = _create_semaphore(configuration)
    return create_openai_chat_llm(
        client, configuration, cache, limiter, semaphore, on_error=on_error
    )


def _create_openai_completion_llm(
    configuration: OpenAIConfiguration,
    on_error: ErrorHandlerFn,
    cache: LLMCache,
    azure=False,
) -> CompletionLLM:
    """创建OpenAI补全LLM."""
    client = create_openai_client(configuration=configuration, azure=azure)
    limiter = _create_limiter(configuration)
    semaphore = _create_semaphore(configuration)
    return create_openai_completion_llm(
        client, configuration, cache, limiter, semaphore, on_error=on_error
    )


def _create_openai_embeddings_llm(
    configuration: OpenAIConfiguration,
    on_error: ErrorHandlerFn,
    cache: LLMCache,
    azure=False,
) -> EmbeddingLLM:
    """创建OpenAI嵌入LLM."""
    client = create_openai_client(configuration=configuration, azure=azure)
    limiter = _create_limiter(configuration)
    semaphore = _create_semaphore(configuration)
    return create_openai_embedding_llm(
        client, configuration, cache, limiter, semaphore, on_error=on_error
    )


def _get_semaphore_or_limiter_name(configuration: OpenAIConfiguration) -> str:
    """
    解决多线程环境这个报错的问题:raise RuntimeError(f'{self!r} is bound to a different event loop')。
    todo liangyuxiang 暂时解决,需要看看过期的semaphore如何销毁,并且还需要关注其他的任务有没有多线程的问题!!!
    """
    task_factory = _get_task_factory()
    task = task_factory.get_task(threading.current_thread())
    if task:
        limit_name = task.taskId
    else:
        print("ERROR _get_limiter_name->任务不存在")
        log.info("ERROR _get_limiter_name->任务不存在")
        limit_name = configuration.model or configuration.deployment_name or "default"

    return limit_name


def _create_limiter(configuration: OpenAIConfiguration) -> LLMLimiter:
    # 限制名称 = 配置模型或配置部署名称或"默认"
    """
    创建limiter。

    Args:
        configuration (OpenAIConfiguration): configuration 参数。

    Returns:
        处理结果。
    """
    limit_name = _get_semaphore_or_limiter_name(configuration)
    if limit_name not in _rate_limiters:
        tpm = configuration.tokens_per_minute
        rpm = configuration.requests_per_minute
        log.info("create TPM/RPM limiter for %s: TPM=%s, RPM=%s", limit_name, tpm, rpm)
        _rate_limiters[limit_name] = create_tpm_rpm_limiters(configuration)
    return _rate_limiters[limit_name]


def _create_semaphore(configuration: OpenAIConfiguration) -> asyncio.Semaphore | None:
    # 限制名称 = 配置模型或配置部署名称或"默认"
    """
    创建semaphore。

    Args:
        configuration (OpenAIConfiguration): configuration 参数。

    Returns:
        处理结果。
    """
    limit_name = _get_semaphore_or_limiter_name(configuration)
    concurrency = configuration.concurrent_requests

    # 如果并发为零,则绕过信号量
    if not concurrency:
        log.info("no concurrency limiter for %s", limit_name)
        return None

    if limit_name not in _semaphores:
        log.info("create concurrency limiter for %s: %s", limit_name, concurrency)
        _semaphores[limit_name] = asyncio.Semaphore(concurrency)

    return _semaphores[limit_name]
