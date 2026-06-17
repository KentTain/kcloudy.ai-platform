"""编排上下文构建器。

Orchestration Context Builders.
"""

from enum import Enum

from ai.components.graphrag.config import GraphRagConfig
from ai.components.graphrag.model import Entity, Relationship
from ai.components.graphrag.query.input.retrieval.entities import (
    get_entity_by_key,
    get_entity_by_name,
)
from ai.components.graphrag.query.llm.base import BaseTextEmbedding
from ai.components.graphrag.vector_stores import (
    BaseVectorStore,
    VectorStoreSearchResult,
)


class EntityVectorStoreKey(str, Enum):
    """
    实体嵌入向量存储中使用的键枚举。

    Keys used as ids in the entity embedding vectorstores.
    """

    ID = "id"
    TITLE = "title"

    @staticmethod
    def from_string(value: str) -> "EntityVectorStoreKey":
        """
        将字符串转换为 EntityVectorStoreKey。

        Convert string to EntityVectorStoreKey.

        参数 Parameters
        ----------
        - value (str): 键字符串。Key string

        返回 Returns
        -------
        - EntityVectorStoreKey: 实体向量存储键枚举值。EntityVectorStoreKey enum value

        异常 Raises
        ------
        - ValueError: 如果键值无效。If key value is invalid
        """
        if value == "id":
            return EntityVectorStoreKey.ID
        if value == "title":
            return EntityVectorStoreKey.TITLE

        msg = f"Invalid EntityVectorStoreKey: {value}"
        raise ValueError(msg)


def map_query_to_entities(
    query: str,
    text_embedding_vectorstore: BaseVectorStore,
    text_embedder: BaseTextEmbedding,
    all_entities: list[Entity],
    embedding_vectorstore_key: str = EntityVectorStoreKey.ID,
    include_entity_names: list[str] | None = None,
    exclude_entity_names: list[str] | None = None,
    k: int = 10,
    oversample_scaler: int = 2,
    config: GraphRagConfig = None,
) -> list[Entity]:
    """
    使用查询和实体描述的文本嵌入的语义相似性来提取匹配给定查询的实体。

    Extract entities that match a given query using semantic similarity of text embeddings of query and entity descriptions.

    参数 Parameters
    ----------
    - query (str): 查询字符串。Query string
    - text_embedding_vectorstore (BaseVectorStore): 文本嵌入向量存储。Text embedding vectorstore
    - text_embedder (BaseTextEmbedding): 文本嵌入器。Text embedder
    - all_entities (list[Entity]): 所有实体列表。All entities list
    - embedding_vectorstore_key (str): 向量存储键类型。Vectorstore key type
    - include_entity_names (list[str] | None): 要包含的实体名称列表。Entity names to include
    - exclude_entity_names (list[str] | None): 要排除的实体名称列表。Entity names to exclude
    - k (int): 返回的实体数量。Number of entities to return
    - oversample_scaler (int): 过采样倍数。Oversample scaler
    - config (GraphRagConfig): GraphRAG 配置。GraphRAG config

    返回 Returns
    -------
    - list[Entity]: 匹配的实体列表。Matched entities list
    """
    if include_entity_names is None:
        include_entity_names = []
    if exclude_entity_names is None:
        exclude_entity_names = []
    matched_entities = []

    if query != "":
        # 获取与查询语义相似度最高的实体 / get entities with highest semantic similarity to query
        # 过采样以考虑排除的实体 / oversample to account for excluded entities
        search_results = text_embedding_vectorstore.similarity_search_by_text(
            text=query,
            text_embedder=lambda t: text_embedder.embed(t),
            k=k * oversample_scaler,
        )

        # 使用重排序器过滤实体 / filter out excluded entities
        search_results = _filter_entities_with_reranker(search_results, query, config)

        for result in search_results:
            matched = get_entity_by_key(
                entities=all_entities,
                key=embedding_vectorstore_key,
                value=result.document.id,
            )
            if matched:
                matched_entities.append(matched)
    else:
        # 查询为空时,按排名排序返回前 k 个实体 / When query is empty, sort by rank and return top k
        all_entities.sort(key=lambda x: x.rank if x.rank else 0, reverse=True)
        matched_entities = all_entities[:k]

    # 过滤掉排除的实体 / filter out excluded entities
    if exclude_entity_names:
        matched_entities = [
            entity
            for entity in matched_entities
            if entity.title not in exclude_entity_names
        ]

    # 添加包含列表中的实体 / add entities in the include_entity list
    included_entities = []
    for entity_name in include_entity_names:
        included_entities.extend(get_entity_by_name(all_entities, entity_name))
    return included_entities + matched_entities


def _filter_entities_with_reranker(
    result: list[VectorStoreSearchResult], query: str, config: GraphRagConfig = None
) -> list[VectorStoreSearchResult]:
    """
    使用重排序器过滤实体。

    Filter entities with reranker.

    参数 Parameters
    ----------
    - result (list[VectorStoreSearchResult]): 向量搜索结果列表。Vector search results list
    - query (str): 查询字符串。Query string
    - config (GraphRagConfig): GraphRAG 配置。GraphRAG config

    返回 Returns
    -------
    - list[VectorStoreSearchResult]: 过滤后的结果列表。Filtered results list
    """
    if config and config.reranker.api_url:
        print(
            f"Using reranker, model: {config.reranker.model}, min_score: {config.reranker.min_score}, size:{len(result)}"
        )
        from ai.components.graphrag.vector_stores.bge_reranker import BgeReranker

        # 使用 BGE 重排序器重新排序结果 / Use BGE reranker to rerank results
        result = BgeReranker(
            api_url=config.reranker.api_url, model_name=config.reranker.model
        ).rerank(result, query)

        if result:
            # 过滤掉相关性得分低的实体
            # Filter out entities with low relevance score
            # TODO liangyuxiang: 此处的过滤并不是很好,因为在知识图谱中,如果是有层级关系的那种内容,与问题不那么相关,也有可能有用!
            # TODO liangyuxiang: This filtering is not ideal, because in knowledge graphs, content with hierarchical relationships may be useful even if not directly relevant to the question!
            result = [
                r
                for r in result
                if r.document.attributes["relevance_score"] > config.reranker.min_score
            ]
            # 此处经过验证,score小于0时,内容跟问题一点关系都没有,所以此处直接过滤掉
            # Verified that when score is less than 0, content has no relation to the question, so filter directly
            result = [r for r in result if r.score > 0]

            print(
                f"After reranker, min_score: {config.reranker.min_score}, size: {len(result)}"
            )

            # 按相关性得分降序排序 / Sort by relevance score in descending order
            result.sort(
                key=lambda x: x.document.attributes["relevance_score"], reverse=True
            )
        return result
    return result


def find_nearest_neighbors_by_graph_embeddings(
    entity_id: str,
    graph_embedding_vectorstore: BaseVectorStore,
    all_entities: list[Entity],
    exclude_entity_names: list[str] | None = None,
    embedding_vectorstore_key: str = EntityVectorStoreKey.ID,
    k: int = 10,
    oversample_scaler: int = 2,
) -> list[Entity]:
    """
    通过图嵌入检索相关实体。

    Retrieve related entities by graph embeddings.

    参数 Parameters
    ----------
    - entity_id (str): 实体 ID。Entity ID
    - graph_embedding_vectorstore (BaseVectorStore): 图嵌入向量存储。Graph embedding vectorstore
    - all_entities (list[Entity]): 所有实体列表。All entities list
    - exclude_entity_names (list[str] | None): 要排除的实体名称列表。Entity names to exclude
    - embedding_vectorstore_key (str): 向量存储键类型。Vectorstore key type
    - k (int): 返回的实体数量。Number of entities to return
    - oversample_scaler (int): 过采样倍数。Oversample scaler

    返回 Returns
    -------
    - list[Entity]: 最近邻实体列表。Nearest neighbor entities list
    """
    if exclude_entity_names is None:
        exclude_entity_names = []
    # 使用图嵌入查找该实体的最近邻 / find nearest neighbors of this entity using graph embedding
    query_entity = get_entity_by_key(
        entities=all_entities, key=embedding_vectorstore_key, value=entity_id
    )
    query_embedding = query_entity.graph_embedding if query_entity else None

    # 过采样以考虑排除的实体 / oversample to account for excluded entities
    if query_embedding:
        matched_entities = []
        search_results = graph_embedding_vectorstore.similarity_search_by_vector(
            query_embedding=query_embedding, k=k * oversample_scaler
        )
        for result in search_results:
            matched = get_entity_by_key(
                entities=all_entities,
                key=embedding_vectorstore_key,
                value=result.document.id,
            )
            if matched:
                matched_entities.append(matched)

        # 过滤掉排除的实体 / filter out excluded entities
        if exclude_entity_names:
            matched_entities = [
                entity
                for entity in matched_entities
                if entity.title not in exclude_entity_names
            ]
        # 按排名降序排序 / Sort by rank in descending order
        matched_entities.sort(key=lambda x: x.rank, reverse=True)
        return matched_entities[:k]

    return []


def find_nearest_neighbors_by_entity_rank(
    entity_name: str,
    all_entities: list[Entity],
    all_relationships: list[Relationship],
    exclude_entity_names: list[str] | None = None,
    k: int | None = 10,
) -> list[Entity]:
    """
    检索与目标实体有直接连接的实体,按实体排名排序。

    Retrieve entities that have direct connections with the target entity, sorted by entity rank.

    参数 Parameters
    ----------
    - entity_name (str): 目标实体名称。Target entity name
    - all_entities (list[Entity]): 所有实体列表。All entities list
    - all_relationships (list[Relationship]): 所有关系列表。All relationships list
    - exclude_entity_names (list[str] | None): 要排除的实体名称列表。Entity names to exclude
    - k (int | None): 返回的实体数量。Number of entities to return

    返回 Returns
    -------
    - list[Entity]: 最近邻实体列表。Nearest neighbor entities list
    """
    if exclude_entity_names is None:
        exclude_entity_names = []
    # 获取与目标实体相关的所有关系 / Get all relationships related to the target entity
    entity_relationships = [
        rel for rel in all_relationships if entity_name in (rel.source, rel.target)
    ]
    # 提取源实体名称集合 / Extract source entity names set
    source_entity_names = {rel.source for rel in entity_relationships}
    # 提取目标实体名称集合 / Extract target entity names set
    target_entity_names = {rel.target for rel in entity_relationships}
    # 合并源和目标实体名称,并排除指定的实体 / Combine source and target entity names, excluding specified entities
    related_entity_names = (source_entity_names.union(target_entity_names)).difference(
        set(exclude_entity_names)
    )
    # 获取相关实体对象 / Get related entity objects
    top_relations = [
        entity for entity in all_entities if entity.title in related_entity_names
    ]
    # 按排名降序排序 / Sort by rank in descending order
    top_relations.sort(key=lambda x: x.rank if x.rank else 0, reverse=True)
    if k:
        return top_relations[:k]
    return top_relations
