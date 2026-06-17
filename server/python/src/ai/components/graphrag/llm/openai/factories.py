"""OpenAI LLM 工厂函数模块。

本模块提供创建各种 OpenAI LLM 实例的工厂函数,包括:
- Chat LLM: 基于聊天的语言模型
- Completion LLM: 基于补全的语言模型
- Embedding LLM: 文本嵌入模型

工厂函数支持配置缓存,速率限制,错误处理等功能,并自动组合
多个装饰器 LLM 实现完整的功能链。
"""

import asyncio

from ai.components.graphrag.llm.base import CachingLLM, RateLimitingLLM
from ai.components.graphrag.llm.limiting import LLMLimiter
from ai.components.graphrag.llm.openai.json_parsing_llm import JsonParsingLLM
from ai.components.graphrag.llm.openai.openai_chat_llm import OpenAIChatLLM
from ai.components.graphrag.llm.openai.openai_completion_llm import (
    OpenAICompletionLLM,
)
from ai.components.graphrag.llm.openai.openai_configuration import OpenAIConfiguration
from ai.components.graphrag.llm.openai.openai_embeddings_llm import (
    OpenAIEmbeddingsLLM,
)
from ai.components.graphrag.llm.openai.openai_history_tracking_llm import (
    OpenAIHistoryTrackingLLM,
)
from ai.components.graphrag.llm.openai.openai_token_replacing_llm import (
    OpenAITokenReplacingLLM,
)
from ai.components.graphrag.llm.openai.types import OpenAIClientTypes
from ai.components.graphrag.llm.openai.utils import (
    RATE_LIMIT_ERRORS,
    RETRYABLE_ERRORS,
    get_completion_cache_args,
    get_sleep_time_from_error,
    get_token_counter,
)
from ai.components.graphrag.llm.types import (
    LLM,
    CompletionLLM,
    EmbeddingLLM,
    ErrorHandlerFn,
    LLMCache,
    LLMInvocationFn,
    OnCacheActionFn,
)


def create_openai_chat_llm(
    client: OpenAIClientTypes,
    config: OpenAIConfiguration,
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
    semaphore: asyncio.Semaphore | None = None,
    on_invoke: LLMInvocationFn | None = None,
    on_error: ErrorHandlerFn | None = None,
    on_cache_hit: OnCacheActionFn | None = None,
    on_cache_miss: OnCacheActionFn | None = None,
) -> CompletionLLM:
    """
    创建openai_chat_llm。

    Args:
        client (OpenAIClientTypes): client 参数。
        config (OpenAIConfiguration): config 参数。
        cache (LLMCache | None): cache 参数。
        limiter (LLMLimiter | None): limiter 参数。
        semaphore (asyncio.Semaphore | None): semaphore 参数。
        on_invoke (LLMInvocationFn | None): on_invoke 参数。
        on_error (ErrorHandlerFn | None): on_error 参数。
        on_cache_hit (OnCacheActionFn | None): on_cache_hit 参数。
        on_cache_miss (OnCacheActionFn | None): on_cache_miss 参数。

    Returns:
        处理结果。
    """
    operation = "chat"
    result = OpenAIChatLLM(client, config)
    result.on_error(on_error)
    if limiter is not None or semaphore is not None:
        result = _rate_limited(result, config, operation, limiter, semaphore, on_invoke)
    if cache is not None:
        result = _cached(result, config, operation, cache, on_cache_hit, on_cache_miss)
    result = OpenAIHistoryTrackingLLM(result)
    result = OpenAITokenReplacingLLM(result)
    return JsonParsingLLM(result)


def create_openai_completion_llm(
    client: OpenAIClientTypes,
    config: OpenAIConfiguration,
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
    semaphore: asyncio.Semaphore | None = None,
    on_invoke: LLMInvocationFn | None = None,
    on_error: ErrorHandlerFn | None = None,
    on_cache_hit: OnCacheActionFn | None = None,
    on_cache_miss: OnCacheActionFn | None = None,
) -> CompletionLLM:
    """
    创建openai_completion_llm。

    Args:
        client (OpenAIClientTypes): client 参数。
        config (OpenAIConfiguration): config 参数。
        cache (LLMCache | None): cache 参数。
        limiter (LLMLimiter | None): limiter 参数。
        semaphore (asyncio.Semaphore | None): semaphore 参数。
        on_invoke (LLMInvocationFn | None): on_invoke 参数。
        on_error (ErrorHandlerFn | None): on_error 参数。
        on_cache_hit (OnCacheActionFn | None): on_cache_hit 参数。
        on_cache_miss (OnCacheActionFn | None): on_cache_miss 参数。

    Returns:
        处理结果。
    """
    operation = "completion"
    result = OpenAICompletionLLM(client, config)
    result.on_error(on_error)
    if limiter is not None or semaphore is not None:
        result = _rate_limited(result, config, operation, limiter, semaphore, on_invoke)
    if cache is not None:
        result = _cached(result, config, operation, cache, on_cache_hit, on_cache_miss)
    return OpenAITokenReplacingLLM(result)


def create_openai_embedding_llm(
    client: OpenAIClientTypes,
    config: OpenAIConfiguration,
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
    semaphore: asyncio.Semaphore | None = None,
    on_invoke: LLMInvocationFn | None = None,
    on_error: ErrorHandlerFn | None = None,
    on_cache_hit: OnCacheActionFn | None = None,
    on_cache_miss: OnCacheActionFn | None = None,
) -> EmbeddingLLM:
    """
    创建openai_embedding_llm。

    Args:
        client (OpenAIClientTypes): client 参数。
        config (OpenAIConfiguration): config 参数。
        cache (LLMCache | None): cache 参数。
        limiter (LLMLimiter | None): limiter 参数。
        semaphore (asyncio.Semaphore | None): semaphore 参数。
        on_invoke (LLMInvocationFn | None): on_invoke 参数。
        on_error (ErrorHandlerFn | None): on_error 参数。
        on_cache_hit (OnCacheActionFn | None): on_cache_hit 参数。
        on_cache_miss (OnCacheActionFn | None): on_cache_miss 参数。

    Returns:
        处理结果。
    """
    operation = "embedding"
    result = OpenAIEmbeddingsLLM(client, config)
    result.on_error(on_error)
    if limiter is not None or semaphore is not None:
        result = _rate_limited(result, config, operation, limiter, semaphore, on_invoke)
    if cache is not None:
        result = _cached(result, config, operation, cache, on_cache_hit, on_cache_miss)
    return result


def _rate_limited(
    delegate: LLM,
    config: OpenAIConfiguration,
    operation: str,
    limiter: LLMLimiter | None,
    semaphore: asyncio.Semaphore | None,
    on_invoke: LLMInvocationFn | None,
):
    """
    处理rate_limited。

    Args:
        delegate (LLM): delegate 参数。
        config (OpenAIConfiguration): config 参数。
        operation (str): operation 参数。
        limiter (LLMLimiter | None): limiter 参数。
        semaphore (asyncio.Semaphore | None): semaphore 参数。
        on_invoke (LLMInvocationFn | None): on_invoke 参数。

    Returns:
        处理结果。
    """
    result = RateLimitingLLM(
        delegate,
        config,
        operation,
        RETRYABLE_ERRORS,
        RATE_LIMIT_ERRORS,
        limiter,
        semaphore,
        get_token_counter(config),
        get_sleep_time_from_error,
    )
    result.on_invoke(on_invoke)
    return result


def _cached(
    delegate: LLM,
    config: OpenAIConfiguration,
    operation: str,
    cache: LLMCache,
    on_cache_hit: OnCacheActionFn | None,
    on_cache_miss: OnCacheActionFn | None,
):
    """
    处理cached。

    Args:
        delegate (LLM): delegate 参数。
        config (OpenAIConfiguration): config 参数。
        operation (str): operation 参数。
        cache (LLMCache): cache 参数。
        on_cache_hit (OnCacheActionFn | None): on_cache_hit 参数。
        on_cache_miss (OnCacheActionFn | None): on_cache_miss 参数。

    Returns:
        处理结果。
    """
    cache_args = get_completion_cache_args(config)
    result = CachingLLM(delegate, cache_args, operation, cache)
    result.on_cache_hit(on_cache_hit)
    result.on_cache_miss(on_cache_miss)
    return result
