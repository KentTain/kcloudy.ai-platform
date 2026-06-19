"""向量存储的基类。

Base classes for vector stores.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ai.components.graphrag.model.types import TextEmbedder

DEFAULT_VECTOR_SIZE: int = 1536


@dataclass
class VectorStoreDocument:
    """
    存储在向量存储中的文档。

    A document that is stored in vector storage.
    """

    id: str | int
    """文档的唯一 ID。unique id for the document"""

    text: str | None
    vector: list[float] | None

    attributes: dict[str, Any] = field(default_factory=dict)
    """存储任何其他元数据,例如标题,日期范围等。store any additional metadata, e.g. title, date ranges, etc"""


@dataclass
class VectorStoreSearchResult:
    """
    向量存储搜索结果。

    A vector storage search result.
    """

    document: VectorStoreDocument
    """找到的文档。Document that was found."""

    score: float
    """介于 0 和 1 之间的相似度得分。越高表示越相似。Similarity score between 0 and 1. Higher is more similar."""


class BaseVectorStore(ABC):
    """
    向量存储数据访问类的基类。

    The base class for vector storage data-access classes.
    """

    def __init__(
        self,
        collection_name: str,
        db_connection: Any | None = None,
        document_collection: Any | None = None,
        query_filter: Any | None = None,
        **kwargs: Any,
    ):
        """
        初始化实例。

        Args:
            collection_name (str): collection_name 参数。
            db_connection (Any | None): db_connection 参数。
            document_collection (Any | None): document_collection 参数。
            query_filter (Any | None): query_filter 参数。
            kwargs (Any): kwargs 参数。
        """
        self.collection_name = collection_name
        self.db_connection = db_connection
        self.document_collection = document_collection
        self.query_filter = query_filter
        self.kwargs = kwargs

    @abstractmethod
    def connect(self, **kwargs: Any) -> None:
        """
        连接到向量存储。

        Connect to vector storage.
        """

    @abstractmethod
    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """
        将文档加载到向量存储中。

        Load documents into the vector-store.
        """

    @abstractmethod
    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """
        通过向量执行近似最近邻搜索。

        Perform ANN search by vector.
        """

    @abstractmethod
    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """
        通过文本执行近似最近邻搜索。

        Perform ANN search by text.
        """

    @abstractmethod
    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """
        构建查询过滤器以按 ID 过滤文档。

        Build a query filter to filter documents by id.
        """
