from ai_plugin.sdk.entities.model import EmbeddingInputType
from ai_plugin.sdk.entities.model.text_embedding import (
    TextEmbeddingModelConfig,
    TextEmbeddingResult,
)
from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class TextEmbeddingInvocation(BackwardsInvocation[TextEmbeddingResult]):
    """文本嵌入调用类

    用于调用文本嵌入模型，将文本转换为向量表示。
    """

    def invoke(
        self,
        model_config: TextEmbeddingModelConfig,
        texts: list[str],
        input_type: EmbeddingInputType = EmbeddingInputType.QUERY,
    ) -> TextEmbeddingResult:
        """调用文本嵌入模型

        Args:
            model_config: 文本嵌入模型配置对象
            texts: 需要嵌入的文本列表
            input_type: 输入类型，默认为查询类型

        Returns:
            文本嵌入结果对象，包含向量表示

        Raises:
            Exception: 当文本嵌入模型没有响应时抛出异常
        """
        # 调用后端文本嵌入服务
        for data in self._backwards_invoke(
            InvokeType.TextEmbedding,
            TextEmbeddingResult,
            {
                **model_config.model_dump(),
                "texts": texts,
                "input_type": input_type.value,
            },
        ):
            return data

        raise Exception("文本嵌入模型没有响应")
