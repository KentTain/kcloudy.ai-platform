from ai_plugin.sdk.entities.model.rerank import RerankModelConfig, RerankResult
from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class RerankInvocation(BackwardsInvocation[RerankResult]):
    """重排序调用类

    用于调用重排序模型，根据查询对文档列表进行相关性排序。
    """

    def invoke(
        self, model_config: RerankModelConfig, docs: list[str], query: str
    ) -> RerankResult:
        """调用重排序模型

        Args:
            model_config: 重排序模型配置对象
            docs: 需要排序的文档列表
            query: 查询文本，用于计算相关性

        Returns:
            重排序结果对象，包含排序后的文档和相关性分数

        Raises:
            Exception: 当重排序模型没有响应时抛出异常
        """
        # 调用后端重排序服务
        for data in self._backwards_invoke(
            InvokeType.Rerank,
            RerankResult,
            {
                **model_config.model_dump(),
                "docs": docs,
                "query": query,
            },
        ):
            return data

        raise Exception("重排序模型没有响应")
