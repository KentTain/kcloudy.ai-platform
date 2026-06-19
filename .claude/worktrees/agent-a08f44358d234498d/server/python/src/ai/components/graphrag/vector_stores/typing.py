"""包含支持的向量存储类型的包。

A package containing the supported vector store types.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from ai.components.graphrag.vector_stores.lancedb import LanceDBVectorStore

if TYPE_CHECKING:
    from ai.components.graphrag.vector_stores.azure_ai_search import AzureAISearch


class VectorStoreType(str, Enum):
    """
    支持的向量存储类型。

    The supported vector store types.
    """

    LanceDB = "lancedb"
    AzureAISearch = "azure_ai_search"


def get_azure_ai_search():
    """
    延迟导入 AzureAISearch，避免启动时加载 Azure 依赖。

    Lazily import AzureAISearch to avoid loading Azure dependencies at startup.
    """
    try:
        from ai.components.graphrag.vector_stores.azure_ai_search import AzureAISearch

        return AzureAISearch
    except ImportError as e:
        msg = "Azure AI Search 依赖未安装，请执行: pip install azure-search-documents azure-identity"
        raise ImportError(msg) from e


class VectorStoreFactory:
    """
    用于创建向量存储的工厂类。

    A factory class for creating vector stores.
    """

    vector_store_types: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, vector_store_type: str, vector_store: type):
        """
        注册向量存储类型。

        Register a vector store type.
        """
        cls.vector_store_types[vector_store_type] = vector_store

    @classmethod
    def get_vector_store(
        cls, vector_store_type: VectorStoreType | str, kwargs: dict
    ) -> LanceDBVectorStore | AzureAISearch:
        """
        从字符串获取向量存储类型。

        Get the vector store type from a string.
        """
        match vector_store_type:
            case VectorStoreType.LanceDB:
                return LanceDBVectorStore(**kwargs)
            case VectorStoreType.AzureAISearch:
                AzureAISearch = get_azure_ai_search()
                return AzureAISearch(**kwargs)
            case _:
                if vector_store_type in cls.vector_store_types:
                    return cls.vector_store_types[vector_store_type](**kwargs)
                msg = f"Unknown vector store type: {vector_store_type}"
                raise ValueError(msg)
