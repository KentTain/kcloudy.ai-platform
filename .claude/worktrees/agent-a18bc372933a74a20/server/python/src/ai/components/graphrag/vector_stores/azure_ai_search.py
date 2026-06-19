"""包含 Azure AI Search 向量存储实现的包。

A package containing the Azure AI Search vector store implementation.
"""

import json
from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from ai.components.graphrag.model.types import TextEmbedder
from ai.components.graphrag.vector_stores.base import (
    DEFAULT_VECTOR_SIZE,
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class AzureAISearch(BaseVectorStore):
    """
    Azure AI Search 向量存储实现。

    The Azure AI Search vector storage implementation.
    """

    index_client: SearchIndexClient

    def connect(self, **kwargs: Any) -> Any:
        """
        连接到 Azure AI 向量存储。

        Connect to the AzureAI vector store.
        """
        url = kwargs.get("url")
        api_key = kwargs.get("api_key")
        audience = kwargs.get("audience")
        self.vector_size = kwargs.get("vector_size", DEFAULT_VECTOR_SIZE)

        self.vector_search_profile_name = kwargs.get(
            "vector_search_profile_name", "vectorSearchProfile"
        )

        if url:
            audience_arg = {"audience": audience} if audience else {}
            self.db_connection = SearchClient(
                endpoint=url,
                index_name=self.collection_name,
                credential=AzureKeyCredential(api_key)
                if api_key
                else DefaultAzureCredential(),
                **audience_arg,
            )
            self.index_client = SearchIndexClient(
                endpoint=url,
                credential=AzureKeyCredential(api_key)
                if api_key
                else DefaultAzureCredential(),
                **audience_arg,
            )
        else:
            not_supported_error = "AAISearchDBClient is not supported on local host."
            raise ValueError(not_supported_error)

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """
        将文档加载到 Azure AI Search 索引中。

        Load documents into the Azure AI Search index.
        """
        if overwrite:
            if self.collection_name in self.index_client.list_index_names():
                self.index_client.delete_index(self.collection_name)

            # 配置向量搜索配置文件 / Configure the vector search profile
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="HnswAlg",
                        parameters=HnswParameters(
                            metric=VectorSearchAlgorithmMetric.COSINE
                        ),
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name=self.vector_search_profile_name,
                        algorithm_configuration_name="HnswAlg",
                    )
                ],
            )

            index = SearchIndex(
                name=self.collection_name,
                fields=[
                    SimpleField(
                        name="id",
                        type=SearchFieldDataType.String,
                        key=True,
                    ),
                    SearchField(
                        name="vector",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True,
                        vector_search_dimensions=self.vector_size,
                        vector_search_profile_name=self.vector_search_profile_name,
                    ),
                    SearchableField(name="text", type=SearchFieldDataType.String),
                    SimpleField(
                        name="attributes",
                        type=SearchFieldDataType.String,
                    ),
                ],
                vector_search=vector_search,
            )

            self.index_client.create_or_update_index(
                index,
            )

        batch = [
            {
                "id": doc.id,
                "vector": doc.vector,
                "text": doc.text,
                "attributes": json.dumps(doc.attributes, ensure_ascii=False),
            }
            for doc in documents
            if doc.vector is not None
        ]

        if batch and len(batch) > 0:
            self.db_connection.upload_documents(batch)

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """
        构建查询过滤器以按 ID 列表过滤文档。

        Build a query filter to filter documents by a list of ids.
        """
        if include_ids is None or len(include_ids) == 0:
            self.query_filter = None
            # 返回以保持与其他方法的一致性,但并非必需 / Returning to keep consistency with other methods, but not needed
            return self.query_filter

        # 有关 odata 过滤的更多信息,请访问: https://learn.microsoft.com/en-us/azure/search/search-query-odata-search-in-function
        # search.in 比连接的 and/or 条件更快 / More info about odata filtering here: search.in is faster that joined and/or conditions
        id_filter = ",".join([f"{id!s}" for id in include_ids])
        self.query_filter = f"search.in(id, '{id_filter}', ',')"

        # 返回以保持与其他方法的一致性,但并非必需 / Returning to keep consistency with other methods, but not needed
        # TODO: 在将来的 PR 中重构 / Refactor on a future PR
        return self.query_filter

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """
        执行基于向量的相似度搜索。

        Perform a vector-based similarity search.
        """
        vectorized_query = VectorizedQuery(
            vector=query_embedding, k_nearest_neighbors=k, fields="vector"
        )

        response = self.db_connection.search(
            vector_queries=[vectorized_query],
        )

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc.get("id", ""),
                    text=doc.get("text", ""),
                    vector=doc.get("vector", []),
                    attributes=(json.loads(doc.get("attributes", "{}"))),
                ),
                # 余弦相似度介于 0.333 和 1.000 之间 / Cosine similarity between 0.333 and 1.000
                # https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking#scores-in-a-hybrid-search-results
                score=doc["@search.score"],
            )
            for doc in response
        ]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """
        执行基于文本的相似度搜索。

        Perform a text-based similarity search.
        """
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(
                query_embedding=query_embedding, k=k
            )
        return []
