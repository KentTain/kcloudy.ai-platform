"""GraphRAG 知识模型的通用类型定义。

Common types for the GraphRAG knowledge model.
"""

from collections.abc import Callable

# 文本嵌入器类型定义:接受字符串参数,返回浮点数列表(嵌入向量)
# Text embedder type definition: accepts a string parameter and returns a list of floats (embedding vector)
TextEmbedder = Callable[[str], list[float]]
