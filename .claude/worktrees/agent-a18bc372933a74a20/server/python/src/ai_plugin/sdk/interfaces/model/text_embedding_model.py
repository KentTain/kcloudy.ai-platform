import time
from abc import abstractmethod

from pydantic import ConfigDict

from ai_plugin.sdk.entities.model import (
    EmbeddingInputType,
    ModelPropertyKey,
    ModelType,
)
from ai_plugin.sdk.entities.model.text_embedding import TextEmbeddingResult
from ai_plugin.sdk.interfaces.model.ai_model import AIModel


class TextEmbeddingModel(AIModel):
    """
    文本嵌入模型类

    提供文本嵌入模型的基本接口和功能实现
    """

    model_type: ModelType = ModelType.TEXT_EMBEDDING

    # pydantic配置
    model_config = ConfigDict(protected_namespaces=())

    ############################################################
    #                  可由插件实现的方法                        #
    ############################################################

    @abstractmethod
    def _invoke(
        self,
        model: str,
        credentials: dict,
        texts: list[str],
        user: str | None = None,
        input_type: EmbeddingInputType = EmbeddingInputType.DOCUMENT,
    ) -> TextEmbeddingResult:
        """
        调用文本嵌入模型

        :param model: 模型名称
        :param credentials: 模型凭证
        :param texts: 要嵌入的文本列表
        :param user: 唯一用户ID
        :param input_type: 嵌入输入类型
        :return: 嵌入结果
        """
        raise NotImplementedError

    @abstractmethod
    def get_num_tokens(
        self, model: str, credentials: dict, texts: list[str]
    ) -> list[int]:
        """
        获取给定文本的token数量

        :param model: 模型名称
        :param credentials: 模型凭证
        :param texts: 要嵌入的文本列表
        :return: 每个文本对应的token数量列表
        """
        raise NotImplementedError

    ############################################################
    #                    仅供插件实现使用                        #
    ############################################################

    def _get_context_size(self, model: str, credentials: dict) -> int:
        """
        获取给定嵌入模型的上下文大小

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 上下文大小
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.CONTEXT_SIZE in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.CONTEXT_SIZE]

        return 1000

    def _get_max_chunks(self, model: str, credentials: dict) -> int:
        """
        获取给定嵌入模型的最大块数

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 最大块数
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.MAX_CHUNKS in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.MAX_CHUNKS]

        return 1

    ############################################################
    #                    仅供执行器使用                          #
    ############################################################

    def invoke(
        self,
        model: str,
        credentials: dict,
        texts: list[str],
        user: str | None = None,
        input_type: EmbeddingInputType = EmbeddingInputType.DOCUMENT,
    ) -> TextEmbeddingResult:
        """
        调用文本嵌入模型

        :param model: 模型名称
        :param credentials: 模型凭证
        :param texts: 要嵌入的文本列表
        :param user: 唯一用户ID
        :param input_type: 嵌入输入类型
        :return: 嵌入结果
        """
        self.started_at = time.perf_counter()

        try:
            return self._invoke(model, credentials, texts, user, input_type)
        except Exception as e:
            raise self._transform_invoke_error(e) from e
