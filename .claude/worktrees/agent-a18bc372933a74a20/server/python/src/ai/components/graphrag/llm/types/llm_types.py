"""
LLM 特定类型定义

定义了特定类型的 LLM 输入输出类型别名。
"""

from typing import TypeAlias

from ai.components.graphrag.llm.types.llm import LLM

# 嵌入模型的输入类型:字符串列表
EmbeddingInput: TypeAlias = list[str]
# 嵌入模型的输出类型:浮点数向量列表
EmbeddingOutput: TypeAlias = list[list[float]]
# 补全模型的输入类型:字符串
CompletionInput: TypeAlias = str
# 补全模型的输出类型:字符串
CompletionOutput: TypeAlias = str

# 嵌入 LLM 类型别名
EmbeddingLLM: TypeAlias = LLM[EmbeddingInput, EmbeddingOutput]
# 补全 LLM 类型别名
CompletionLLM: TypeAlias = LLM[CompletionInput, CompletionOutput]
