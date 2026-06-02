import time
from abc import abstractmethod

from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.entities.model.rerank import RerankResult
from ai_plugin.sdk.interfaces.model.ai_model import AIModel


class RerankModel(AIModel):
    """
    重排序模型基类

    提供重排序模型的基本接口和功能实现
    """

    model_type: ModelType = ModelType.RERANK

    ############################################################
    #                  可由插件实现的方法                        #
    ############################################################

    @abstractmethod
    def _invoke(
        self,
        model: str,
        credentials: dict,
        query: str,
        docs: list[str],
        score_threshold: float | None = None,
        top_n: int | None = None,
        user: str | None = None,
    ) -> RerankResult:
        """
        调用重排序模型

        :param model: 模型名称
        :param credentials: 模型凭证
        :param query: 搜索查询
        :param docs: 用于重排序的文档列表
        :param score_threshold: 分数阈值
        :param top_n: 返回前N个结果
        :param user: 唯一用户ID
        :return: 重排序结果
        """
        raise NotImplementedError

    ############################################################
    #                    仅供执行器使用                          #
    ############################################################

    def invoke(
        self,
        model: str,
        credentials: dict,
        query: str,
        docs: list[str],
        score_threshold: float | None = None,
        top_n: int | None = None,
        user: str | None = None,
    ) -> RerankResult:
        """
        调用重排序模型

        :param model: 模型名称
        :param credentials: 模型凭证
        :param query: 搜索查询
        :param docs: 用于重排序的文档列表
        :param score_threshold: 分数阈值
        :param top_n: 返回前N个结果
        :param user: 唯一用户ID
        :return: 重排序结果
        """
        self.started_at = time.perf_counter()

        try:
            return self._invoke(
                model, credentials, query, docs, score_threshold, top_n, user
            )
        except Exception as e:
            raise self._transform_invoke_error(e) from e
