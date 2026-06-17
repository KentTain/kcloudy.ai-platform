"""文本嵌入 LLM 类模块。

本模块实现了基于 OpenAI Embeddings API 的文本嵌入模型。
用于将文本转换为向量表示,支持语义搜索,相似度计算等应用。
"""

from typing import Unpack

from ai.components.graphrag.llm.base import BaseLLM
from ai.components.graphrag.llm.openai.openai_configuration import OpenAIConfiguration
from ai.components.graphrag.llm.openai.types import OpenAIClientTypes
from ai.components.graphrag.llm.types import (
    EmbeddingInput,
    EmbeddingOutput,
    LLMInput,
)


class OpenAIEmbeddingsLLM(BaseLLM[EmbeddingInput, EmbeddingOutput]):
    """
    文本嵌入生成器 LLM。

    使用 OpenAI 的 Embeddings API 将文本转换为高维向量表示。
    支持单个或批量文本的嵌入生成。
    """

    _client: OpenAIClientTypes
    _configuration: OpenAIConfiguration

    def __init__(self, client: OpenAIClientTypes, configuration: OpenAIConfiguration):
        """
        初始化实例。

        Args:
            client (OpenAIClientTypes): client 参数。
            configuration (OpenAIConfiguration): configuration 参数。
        """
        self.client = client
        self.configuration = configuration

    async def _execute_llm(
        self, input: EmbeddingInput, **kwargs: Unpack[LLMInput]
    ) -> EmbeddingOutput | None:
        """
        执行execute_llm。

        Args:
            input (EmbeddingInput): input 参数。
            kwargs (Unpack[LLMInput]): kwargs 参数。

        Returns:
            处理结果。
        """
        args = {
            "model": self.configuration.model,
            **(kwargs.get("model_parameters") or {}),
        }
        embedding = await self.client.embeddings.create(
            input=input,
            **args,
        )
        # 提取所有嵌入向量
        return [d.embedding for d in embedding.data]
