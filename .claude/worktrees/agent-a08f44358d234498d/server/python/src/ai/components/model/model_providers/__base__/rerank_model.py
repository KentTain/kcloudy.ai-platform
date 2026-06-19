from ai.components.model.model_providers.__base__.ai_model import AIModelImpl
from ai.components.plugin.client.model_client import ModelClient
from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.entities.model.rerank import RerankResult


class RerankModelImpl(AIModelImpl):
    """
    重排序模型基础类
    """

    model_type: ModelType = ModelType.RERANK

    async def invoke(
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
        :param docs: 待重排序的文档
        :param score_threshold: 分数阈值
        :param top_n: 前N个结果
        :param user: 唯一用户ID
        :return: 重排序结果
        """

        try:
            model_client = ModelClient()
            return await model_client.invoke_rerank(
                tenant_id=self.tenant_id,
                user_id=user or "unknown",
                plugin_id=self.plugin_id,
                provider=self.provider_name,
                model=model,
                credentials=credentials,
                query=query,
                docs=docs,
                score_threshold=score_threshold,
                top_n=top_n,
            )
        except Exception as e:
            raise self._transform_invoke_error(e)
