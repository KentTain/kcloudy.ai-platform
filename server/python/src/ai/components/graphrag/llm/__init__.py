"""
Datashaper OpenAI 工具包

提供了用于与 LLM(大型语言模型)交互的核心功能,包括:
- 基础 LLM 抽象类
- 缓存和速率限制功能
- OpenAI 客户端封装
- Mock LLM 用于测试
- 限流器(Limiter)实现
"""

from ai.components.graphrag.llm.base import BaseLLM, CachingLLM, RateLimitingLLM
from ai.components.graphrag.llm.errors import RetriesExhaustedError
from ai.components.graphrag.llm.limiting import (
    CompositeLLMLimiter,
    LLMLimiter,
    NoopLLMLimiter,
    TpmRpmLLMLimiter,
    create_tpm_rpm_limiters,
)
from ai.components.graphrag.llm.mock import MockChatLLM, MockCompletionLLM
from ai.components.graphrag.llm.openai import (
    OpenAIChatLLM,
    OpenAIClientTypes,
    OpenAICompletionLLM,
    OpenAIConfiguration,
    OpenAIEmbeddingsLLM,
    create_openai_chat_llm,
    create_openai_client,
    create_openai_completion_llm,
    create_openai_embedding_llm,
)
from ai.components.graphrag.llm.types import (
    LLM,
    CompletionInput,
    CompletionLLM,
    CompletionOutput,
    EmbeddingInput,
    EmbeddingLLM,
    EmbeddingOutput,
    ErrorHandlerFn,
    IsResponseValidFn,
    LLMCache,
    LLMConfig,
    LLMInput,
    LLMInvocationFn,
    LLMInvocationResult,
    LLMOutput,
    OnCacheActionFn,
)

__all__ = [
    # LLM Types
    "LLM",
    "BaseLLM",
    "CachingLLM",
    "CompletionInput",
    "CompletionLLM",
    "CompletionOutput",
    "CompositeLLMLimiter",
    "EmbeddingInput",
    "EmbeddingLLM",
    "EmbeddingOutput",
    # Callbacks
    "ErrorHandlerFn",
    "IsResponseValidFn",
    # Cache
    "LLMCache",
    "LLMConfig",
    # LLM I/O Types
    "LLMInput",
    "LLMInvocationFn",
    "LLMInvocationResult",
    "LLMLimiter",
    "LLMOutput",
    "MockChatLLM",
    # Mock
    "MockCompletionLLM",
    "NoopLLMLimiter",
    "OnCacheActionFn",
    "OpenAIChatLLM",
    "OpenAIClientTypes",
    "OpenAICompletionLLM",
    # OpenAI
    "OpenAIConfiguration",
    "OpenAIEmbeddingsLLM",
    "RateLimitingLLM",
    # Errors
    "RetriesExhaustedError",
    "TpmRpmLLMLimiter",
    "create_openai_chat_llm",
    "create_openai_client",
    "create_openai_completion_llm",
    "create_openai_embedding_llm",
    # Limiters
    "create_tpm_rpm_limiters",
]
