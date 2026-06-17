"""
LLM 类型定义

提供了 LLM 模块使用的所有类型定义:
- LLM: LLM 协议接口
- LLMCache: LLM 缓存接口
- LLMConfig: LLM 配置协议
- LLMInput/LLMOutput: LLM 输入输出类型
- LLMInvocationResult: LLM 调用结果
- CompletionLLM/EmbeddingLLM: 特定类型的 LLM
- 各种回调函数类型
"""

from ai.components.graphrag.llm.types.llm import LLM
from ai.components.graphrag.llm.types.llm_cache import LLMCache
from ai.components.graphrag.llm.types.llm_callbacks import (
    ErrorHandlerFn,
    IsResponseValidFn,
    LLMInvocationFn,
    OnCacheActionFn,
)
from ai.components.graphrag.llm.types.llm_config import LLMConfig
from ai.components.graphrag.llm.types.llm_invocation_result import LLMInvocationResult
from ai.components.graphrag.llm.types.llm_io import (
    LLMInput,
    LLMOutput,
)
from ai.components.graphrag.llm.types.llm_types import (
    CompletionInput,
    CompletionLLM,
    CompletionOutput,
    EmbeddingInput,
    EmbeddingLLM,
    EmbeddingOutput,
)

__all__ = [
    "LLM",
    "CompletionInput",
    "CompletionLLM",
    "CompletionOutput",
    "EmbeddingInput",
    "EmbeddingLLM",
    "EmbeddingOutput",
    "ErrorHandlerFn",
    "IsResponseValidFn",
    "LLMCache",
    "LLMConfig",
    "LLMInput",
    "LLMInvocationFn",
    "LLMInvocationResult",
    "LLMOutput",
    "OnCacheActionFn",
]
