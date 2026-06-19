"""BGE 重排器实现。

BGE Reranker implementation.
"""

from functools import cached_property

import requests

from ai.components.graphrag.vector_stores import VectorStoreSearchResult


class BgeReranker:
    """
    BGE 重排器类,用于对搜索结果进行重新排序。

    BGE Reranker class for reranking search results.
    """

    def __init__(
        self,
        api_url: str | None = None,
        model_name: str | None = None,
    ):
        """
        初始化 BGE 重排器。

        Initialize BGE Reranker.

        参数 Parameters
        ----------
        api_url : str
            重排器 API 的 URL。The URL of the reranker API.
        model_name : str
            使用的模型名称。The model name to use.
        """
        self.model_name = model_name
        self.api_url = api_url

    @cached_property
    def _client(self):
        """
        获取 HTTP 客户端。

        Get HTTP client.
        """
        return requests

    def rerank(self, docs: list[VectorStoreSearchResult], query: str):
        """
        对搜索结果进行重新排序。

        Rerank search results.

        参数 Parameters
        ----------
        docs : list[VectorStoreSearchResult]
            要重新排序的文档列表。List of documents to rerank.
        query : str
            用户查询。User query.

        返回 Returns
        -------
        list[VectorStoreSearchResult]
            重新排序后的文档列表。Reranked list of documents.
        """
        new_docs = [
            {
                "page_content": f"{doc.document.attributes.get('title', '')}:{doc.document.text if doc.document.text else ''}",
                "metadata": {"raw_id": doc.document.id},
            }
            for doc in docs
        ]

        results_list = self._client.post(
            self.api_url,
            json={
                "query": query,
                "documents": new_docs,
                "model": self.model_name,
                "top_n": len(new_docs),
            },
        ).json()

        # 将 results 数组转换为字典 / Convert results array to dictionary
        results_dict = {result["metadata"]["raw_id"]: result for result in results_list}

        for index, doc in enumerate(docs):
            result = results_dict.get(doc.document.id, None)
            if result is None:
                doc.document.attributes["relevance_score"] = 0
            else:
                doc.document.attributes["relevance_score"] = result["metadata"][
                    "relevance_score"
                ]
        return docs
