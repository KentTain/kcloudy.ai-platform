"""
重排序服务
提供所有重排序相关功能的统一接口
"""

from ai.components.model.internal.model_instance_factory import (
    ModelInstance,
    ModelInstanceFactory,
)
from ai.components.model.services.base_model_service import BaseModelService
from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.entities.model.rerank import RerankResult


class RerankService(BaseModelService):
    """
    重排序服务类

    封装所有重排序相关的操作，提供简洁易用的接口
    """

    def __init__(self, tenant_id: str):
        """
        :param tenant_id: 租户 ID
        """
        super().__init__(tenant_id)

    async def rerank(
        self,
        query: str,
        docs: list[str],
        model: str | None = None,
        provider: str | None = None,
        top_n: int | None = None,
        score_threshold: float | None = None,
        user: str | None = None,
    ) -> RerankResult:
        """
        文档重排序接口

        :param query: 搜索查询
        :param docs: 待重排序的文档列表
        :param model: 模型名称（可选）
        :param provider: 供应商名称（可选）
        :param top_n: 返回前N个结果
        :param score_threshold: 分数阈值
        :param user: 用户ID
        :return: 重排序结果
        """

        if not provider or not model:
            provider, model = await self._resolve_default_model(ModelType.RERANK)

        modelInstance: ModelInstance = await self._factory.get_model_instance(
            self._tenant_id,
            provider,
            model_type=ModelType.RERANK,
            model=model,
        )

        result = await modelInstance.invoke_rerank(
            query=query,
            docs=docs,
            score_threshold=score_threshold,
            top_n=top_n,
            user=user,
        )

        return result

    async def score(
        self,
        query: str,
        doc: str,
        model: str | None = None,
        provider: str | None = None,
        user: str | None = None,
    ) -> float:
        """
        单文档相似度打分接口

        :param query: 搜索查询
        :param doc: 文档内容
        :param model: 模型名称（可选）
        :param provider: 供应商名称（可选）
        :param user: 用户ID
        :return: 相似度分数
        """
        result = await self.rerank(
            query=query,
            docs=[doc],
            model=model,
            provider=provider,
            top_n=1,
            user=user,
        )

        if result.docs and len(result.docs) > 0:
            return result.docs[0].score
        return 0.0
