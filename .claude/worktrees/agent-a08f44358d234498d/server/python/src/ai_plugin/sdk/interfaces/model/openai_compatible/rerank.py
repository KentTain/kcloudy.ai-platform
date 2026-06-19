from json import dumps

from requests import HTTPError, post
from yarl import URL

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.sdk.entities.model import AIModelEntity, FetchFrom, ModelType
from ai_plugin.sdk.entities.model.rerank import RerankDocument, RerankResult
from ai_plugin.sdk.errors.model import (
    CredentialsValidateFailedError,
    InvokeError,
    InvokeServerUnavailableError,
)
from ai_plugin.sdk.interfaces.model.rerank_model import RerankModel


class OAICompatRerankModel(RerankModel):
    """
    重排序模型API与Jina重排序模型API兼容。因此在此复制JinaRerankModel类的代码。
    我们需要为llama.cpp进行增强，它返回原始分数而不是标准化的0~1分数。看起来Dify需要这个功能。
    """

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
        :param top_n: 返回前N个文档
        :param user: 唯一用户ID
        :return: 重排序结果
        """
        if len(docs) == 0:
            return RerankResult(model=model, docs=[])

        server_url = credentials["endpoint_url"]
        model_name = model

        if not server_url:
            raise CredentialsValidateFailedError("server_url is required")
        if not model_name:
            raise CredentialsValidateFailedError("model_name is required")

        url = server_url
        headers = {
            "Authorization": f"Bearer {credentials.get('api_key')}",
            "Content-Type": "application/json",
        }

        # 待办：我们是否需要截断文档以避免llama.cpp返回错误？

        data = {
            "model": model_name,
            "query": query,
            "documents": docs,
            "top_n": top_n,
            "return_documents": True,
        }

        try:
            response = post(
                str(URL(url) / "rerank"), headers=headers, data=dumps(data), timeout=60
            )
            response.raise_for_status()
            results = response.json()

            rerank_documents = []
            scores = [result["relevance_score"] for result in results["results"]]

            # 最小-最大标准化：将分数标准化到0~1.0范围
            min_score = min(scores)
            max_score = max(scores)
            score_range = (
                max_score - min_score if max_score != min_score else 1.0
            )  # 避免除以零

            for result in results["results"]:
                index = result["index"]

                # 检索文档文本（如果llama.cpp重排序没有返回，则使用备用方案）
                text = docs[index]
                document = result.get("document", {})
                if document:
                    if isinstance(document, dict):
                        text = document.get("text", docs[index])
                    elif isinstance(document, str):
                        text = document

                # 标准化分数
                normalized_score = (result["relevance_score"] - min_score) / score_range

                # 使用标准化分数创建RerankDocument对象
                rerank_document = RerankDocument(
                    index=index,
                    text=text,
                    score=normalized_score,
                )

                # 应用阈值（如果已定义）
                if score_threshold is None or normalized_score >= score_threshold:
                    rerank_documents.append(rerank_document)

            # 按标准化分数降序排列rerank_documents
            rerank_documents.sort(key=lambda doc: doc.score, reverse=True)

            return RerankResult(model=model, docs=rerank_documents)

        except HTTPError as e:
            raise InvokeServerUnavailableError(str(e)) from e

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        验证模型凭证

        :param model: 模型名称
        :param credentials: 模型凭证
        """
        try:
            self._invoke(
                model=model,
                credentials=credentials,
                query="What is the capital of the United States?",
                docs=[
                    "Carson City is the capital city of the American state of Nevada. At the 2010 United States "
                    "Census, Carson City had a population of 55,274.",
                    "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean that "
                    "are a political division controlled by the United States. Its capital is Saipan.",
                ],
                score_threshold=0.8,
            )
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex)) from ex

    def get_customizable_model_schema(
        self, model: str, credentials: dict
    ) -> AIModelEntity:
        """
        从凭证生成自定义模型实体

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: AI模型实体
        """
        entity = AIModelEntity(
            model=model,
            label=I18nObject(en_US=model),
            model_type=ModelType.RERANK,
            fetch_from=FetchFrom.CUSTOMIZABLE_MODEL,
            model_properties={},
        )

        return entity

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        """
        将模型调用错误映射到统一错误

        :return: 调用错误映射字典
        """
        return {}
