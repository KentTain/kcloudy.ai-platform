"""OpenAI LLM 类型定义模块。

本模块定义了 OpenAI 相关的类型别名和基础类型。
"""

from openai import (
    AsyncAzureOpenAI,
    AsyncOpenAI,
)

# OpenAI 客户端类型联合类型
# 包括标准 OpenAI 客户端和 Azure OpenAI 客户端
OpenAIClientTypes = AsyncOpenAI | AsyncAzureOpenAI
