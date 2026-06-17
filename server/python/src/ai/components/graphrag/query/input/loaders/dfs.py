"""从数据框加载数据到数据对象集合。

Load data from dataframes into collections of data objects.
"""

import pandas as pd

from ai.components.graphrag.model import (
    Community,
    CommunityReport,
    Covariate,
    Document,
    Entity,
    Relationship,
    TextUnit,
)
from ai.components.graphrag.query.input.loaders.utils import (
    to_list,
    to_optional_dict,
    to_optional_float,
    to_optional_int,
    to_optional_list,
    to_optional_str,
    to_str,
)
from ai.components.graphrag.vector_stores import BaseVectorStore, VectorStoreDocument


def read_entities(
    df: pd.DataFrame,
    id_col: str = "id",
    short_id_col: str | None = "short_id",
    title_col: str = "title",
    type_col: str | None = "type",
    description_col: str | None = "description",
    name_embedding_col: str | None = "name_embedding",
    description_embedding_col: str | None = "description_embedding",
    graph_embedding_col: str | None = "graph_embedding",
    community_col: str | None = "community_ids",
    text_unit_ids_col: str | None = "text_unit_ids",
    document_ids_col: str | None = "document_ids",
    rank_col: str | None = "degree",
    attributes_cols: list[str] | None = None,
) -> list[Entity]:
    """
    从数据框读取实体。

    Read entities from a dataframe.

    参数 Parameters
    ----------
    - df (pd.DataFrame): 包含实体数据的数据框。Dataframe containing entity data
    - id_col (str): ID 列名。ID column name
    - short_id_col (str | None): 短 ID 列名。Short ID column name
    - title_col (str): 标题列名。Title column name
    - type_col (str | None): 类型列名。Type column name
    - description_col (str | None): 描述列名。Description column name
    - name_embedding_col (str | None): 名称嵌入列名。Name embedding column name
    - description_embedding_col (str | None): 描述嵌入列名。Description embedding column name
    - graph_embedding_col (str | None): 图嵌入列名。Graph embedding column name
    - community_col (str | None): 社区 ID 列名。Community IDs column name
    - text_unit_ids_col (str | None): 文本单元 ID 列名。Text unit IDs column name
    - document_ids_col (str | None): 文档 ID 列名。Document IDs column name
    - rank_col (str | None): 排名列名。Rank column name
    - attributes_cols (list[str] | None): 属性列名列表。List of attribute column names

    返回 Returns
    -------
    - list[Entity]: 实体列表。List of entities
    """
    entities = []
    for idx, row in df.iterrows():
        entity = Entity(
            id=to_str(row, id_col),
            short_id=to_optional_str(row, short_id_col) if short_id_col else str(idx),
            title=to_str(row, title_col),
            type=to_optional_str(row, type_col),
            description=to_optional_str(row, description_col),
            name_embedding=to_optional_list(row, name_embedding_col, item_type=float),
            description_embedding=to_optional_list(
                row, description_embedding_col, item_type=float
            ),
            graph_embedding=to_optional_list(row, graph_embedding_col, item_type=float),
            community_ids=to_optional_list(row, community_col, item_type=str),
            text_unit_ids=to_optional_list(row, text_unit_ids_col),
            document_ids=to_optional_list(row, document_ids_col),
            rank=to_optional_int(row, rank_col),
            attributes=(
                {col: row.get(col) for col in attributes_cols}
                if attributes_cols
                else None
            ),
            custom_add=row["custom_add"] if row.get("custom_add", None) != None else "",
            custom_update=row["custom_update"]
            if row.get("custom_update", None) != None
            else "",
        )
        entities.append(entity)
    return entities


def store_entity_semantic_embeddings(
    entities: list[Entity],
    vectorstore: BaseVectorStore,
) -> BaseVectorStore:
    """
    将实体语义嵌入存储到向量存储中。

    Store entity semantic embeddings in a vectorstore.

    参数 Parameters
    ----------
    - entities (list[Entity]): 实体列表。List of entities
    - vectorstore (BaseVectorStore): 向量存储实例。Vectorstore instance

    返回 Returns
    -------
    - BaseVectorStore: 加载了数据的向量存储。Vectorstore with loaded data
    """
    documents = [
        VectorStoreDocument(
            id=entity.id,
            text=entity.description,
            vector=entity.description_embedding,
            attributes=(
                {"title": entity.title, **entity.attributes}
                if entity.attributes
                else {"title": entity.title}
            ),
        )
        for entity in entities
    ]
    vectorstore.load_documents(documents=documents)
    return vectorstore


def store_entity_behavior_embeddings(
    entities: list[Entity],
    vectorstore: BaseVectorStore,
) -> BaseVectorStore:
    """
    将实体行为嵌入存储到向量存储中。

    Store entity behavior embeddings in a vectorstore.

    参数 Parameters
    ----------
    - entities (list[Entity]): 实体列表。List of entities
    - vectorstore (BaseVectorStore): 向量存储实例。Vectorstore instance

    返回 Returns
    -------
    - BaseVectorStore: 加载了数据的向量存储。Vectorstore with loaded data
    """
    documents = [
        VectorStoreDocument(
            id=entity.id,
            text=entity.description,
            vector=entity.graph_embedding,
            attributes=(
                {"title": entity.title, **entity.attributes}
                if entity.attributes
                else {"title": entity.title}
            ),
        )
        for entity in entities
    ]
    vectorstore.load_documents(documents=documents)
    return vectorstore


def read_relationships(
    df: pd.DataFrame,
    id_col: str = "id",
    short_id_col: str | None = "short_id",
    source_col: str = "source",
    target_col: str = "target",
    description_col: str | None = "description",
    description_embedding_col: str | None = "description_embedding",
    weight_col: str | None = "weight",
    text_unit_ids_col: str | None = "text_unit_ids",
    document_ids_col: str | None = "document_ids",
    attributes_cols: list[str] | None = None,
) -> list[Relationship]:
    """
    从数据框读取关系。

    Read relationships from a dataframe.

    参数 Parameters
    ----------
    - df (pd.DataFrame): 包含关系数据的数据框。Dataframe containing relationship data
    - id_col (str): ID 列名。ID column name
    - short_id_col (str | None): 短 ID 列名。Short ID column name
    - source_col (str): 源节点列名。Source column name
    - target_col (str): 目标节点列名。Target column name
    - description_col (str | None): 描述列名。Description column name
    - description_embedding_col (str | None): 描述嵌入列名。Description embedding column name
    - weight_col (str | None): 权重列名。Weight column name
    - text_unit_ids_col (str | None): 文本单元 ID 列名。Text unit IDs column name
    - document_ids_col (str | None): 文档 ID 列名。Document IDs column name
    - attributes_cols (list[str] | None): 属性列名列表。List of attribute column names

    返回 Returns
    -------
    - list[Relationship]: 关系列表。List of relationships
    """
    relationships = []
    for idx, row in df.iterrows():
        rel = Relationship(
            id=to_str(row, id_col),
            short_id=to_optional_str(row, short_id_col) if short_id_col else str(idx),
            source=to_str(row, source_col),
            target=to_str(row, target_col),
            description=to_optional_str(row, description_col),
            description_embedding=to_optional_list(
                row, description_embedding_col, item_type=float
            ),
            weight=to_optional_float(row, weight_col),
            text_unit_ids=to_optional_list(row, text_unit_ids_col, item_type=str),
            document_ids=to_optional_list(row, document_ids_col, item_type=str),
            attributes=(
                {col: row.get(col) for col in attributes_cols}
                if attributes_cols
                else None
            ),
            custom_add=row["custom_add"] if row.get("custom_add", None) != None else "",
            custom_update=row["custom_update"]
            if row.get("custom_update", None) != None
            else "",
        )
        relationships.append(rel)
    return relationships


def read_covariates(
    df: pd.DataFrame,
    id_col: str = "id",
    short_id_col: str | None = "short_id",
    subject_col: str = "subject_id",
    subject_type_col: str | None = "subject_type",
    covariate_type_col: str | None = "covariate_type",
    text_unit_ids_col: str | None = "text_unit_ids",
    document_ids_col: str | None = "document_ids",
    attributes_cols: list[str] | None = None,
) -> list[Covariate]:
    """
    从数据框读取协变量。

    Read covariates from a dataframe.

    参数 Parameters
    ----------
    - df (pd.DataFrame): 包含协变量数据的数据框。Dataframe containing covariate data
    - id_col (str): ID 列名。ID column name
    - short_id_col (str | None): 短 ID 列名。Short ID column name
    - subject_col (str): 主体 ID 列名。Subject ID column name
    - subject_type_col (str | None): 主体类型列名。Subject type column name
    - covariate_type_col (str | None): 协变量类型列名。Covariate type column name
    - text_unit_ids_col (str | None): 文本单元 ID 列名。Text unit IDs column name
    - document_ids_col (str | None): 文档 ID 列名。Document IDs column name
    - attributes_cols (list[str] | None): 属性列名列表。List of attribute column names

    返回 Returns
    -------
    - list[Covariate]: 协变量列表。List of covariates
    """
    covariates = []
    for idx, row in df.iterrows():
        cov = Covariate(
            id=to_str(row, id_col),
            short_id=to_optional_str(row, short_id_col) if short_id_col else str(idx),
            subject_id=to_str(row, subject_col),
            subject_type=(
                to_str(row, subject_type_col) if subject_type_col else "entity"
            ),
            covariate_type=(
                to_str(row, covariate_type_col) if covariate_type_col else "claim"
            ),
            text_unit_ids=to_optional_list(row, text_unit_ids_col, item_type=str),
            document_ids=to_optional_list(row, document_ids_col, item_type=str),
            attributes=(
                {col: row.get(col) for col in attributes_cols}
                if attributes_cols
                else None
            ),
        )
        covariates.append(cov)
    return covariates


def read_communities(
    df: pd.DataFrame,
    id_col: str = "id",
    short_id_col: str | None = "short_id",
    title_col: str = "title",
    level_col: str = "level",
    entities_col: str | None = "entity_ids",
    relationships_col: str | None = "relationship_ids",
    covariates_col: str | None = "covariate_ids",
    attributes_cols: list[str] | None = None,
) -> list[Community]:
    """
    从数据框读取社区。

    Read communities from a dataframe.

    参数 Parameters
    ----------
    - df (pd.DataFrame): 包含社区数据的数据框。Dataframe containing community data
    - id_col (str): ID 列名。ID column name
    - short_id_col (str | None): 短 ID 列名。Short ID column name
    - title_col (str): 标题列名。Title column name
    - level_col (str): 层级列名。Level column name
    - entities_col (str | None): 实体 ID 列名。Entity IDs column name
    - relationships_col (str | None): 关系 ID 列名。Relationship IDs column name
    - covariates_col (str | None): 协变量 ID 列名。Covariate IDs column name
    - attributes_cols (list[str] | None): 属性列名列表。List of attribute column names

    返回 Returns
    -------
    - list[Community]: 社区列表。List of communities
    """
    communities = []
    for idx, row in df.iterrows():
        comm = Community(
            id=to_str(row, id_col),
            short_id=to_optional_str(row, short_id_col) if short_id_col else str(idx),
            title=to_str(row, title_col),
            level=to_str(row, level_col),
            entity_ids=to_optional_list(row, entities_col, item_type=str),
            relationship_ids=to_optional_list(row, relationships_col, item_type=str),
            covariate_ids=to_optional_dict(
                row, covariates_col, key_type=str, value_type=str
            ),
            attributes=(
                {col: row.get(col) for col in attributes_cols}
                if attributes_cols
                else None
            ),
        )
        communities.append(comm)
    return communities


def read_community_reports(
    df: pd.DataFrame,
    id_col: str = "id",
    short_id_col: str | None = "short_id",
    title_col: str = "title",
    community_col: str = "community",
    summary_col: str = "summary",
    content_col: str = "full_content",
    rank_col: str | None = "rank",
    summary_embedding_col: str | None = "summary_embedding",
    content_embedding_col: str | None = "full_content_embedding",
    attributes_cols: list[str] | None = None,
) -> list[CommunityReport]:
    """
    从数据框读取社区报告。

    Read community reports from a dataframe.

    参数 Parameters
    ----------
    - df (pd.DataFrame): 包含社区报告数据的数据框。Dataframe containing community report data
    - id_col (str): ID 列名。ID column name
    - short_id_col (str | None): 短 ID 列名。Short ID column name
    - title_col (str): 标题列名。Title column name
    - community_col (str): 社区 ID 列名。Community ID column name
    - summary_col (str): 摘要列名。Summary column name
    - content_col (str): 完整内容列名。Full content column name
    - rank_col (str | None): 排名列名。Rank column name
    - summary_embedding_col (str | None): 摘要嵌入列名。Summary embedding column name
    - content_embedding_col (str | None): 内容嵌入列名。Content embedding column name
    - attributes_cols (list[str] | None): 属性列名列表。List of attribute column names

    返回 Returns
    -------
    - list[CommunityReport]: 社区报告列表。List of community reports
    """
    reports = []
    for idx, row in df.iterrows():
        report = CommunityReport(
            id=to_str(row, id_col),
            short_id=to_optional_str(row, short_id_col) if short_id_col else str(idx),
            title=to_str(row, title_col),
            community_id=to_str(row, community_col),
            summary=to_str(row, summary_col),
            full_content=to_str(row, content_col),
            rank=to_optional_float(row, rank_col),
            summary_embedding=to_optional_list(
                row, summary_embedding_col, item_type=float
            ),
            full_content_embedding=to_optional_list(
                row, content_embedding_col, item_type=float
            ),
            attributes=(
                {col: row.get(col) for col in attributes_cols}
                if attributes_cols
                else None
            ),
            custom_add=row["custom_add"] if row.get("custom_add", None) != None else "",
            custom_update=row["custom_update"]
            if row.get("custom_update", None) != None
            else "",
            report_id=row["id"],
        )
        reports.append(report)
    return reports


def read_text_units(
    df: pd.DataFrame,
    id_col: str = "id",
    short_id_col: str | None = "short_id",
    text_col: str = "text",
    entities_col: str | None = "entity_ids",
    relationships_col: str | None = "relationship_ids",
    covariates_col: str | None = "covariate_ids",
    tokens_col: str | None = "n_tokens",
    document_ids_col: str | None = "document_ids",
    embedding_col: str | None = "text_embedding",
    attributes_cols: list[str] | None = None,
) -> list[TextUnit]:
    """
    从数据框读取文本单元。

    Read text units from a dataframe.

    参数 Parameters
    ----------
    - df (pd.DataFrame): 包含文本单元数据的数据框。Dataframe containing text unit data
    - id_col (str): ID 列名。ID column name
    - short_id_col (str | None): 短 ID 列名。Short ID column name
    - text_col (str): 文本内容列名。Text content column name
    - entities_col (str | None): 实体 ID 列名。Entity IDs column name
    - relationships_col (str | None): 关系 ID 列名。Relationship IDs column name
    - covariates_col (str | None): 协变量 ID 列名。Covariate IDs column name
    - tokens_col (str | None): 令牌数列名。Token count column name
    - document_ids_col (str | None): 文档 ID 列名。Document IDs column name
    - embedding_col (str | None): 嵌入列名。Embedding column name
    - attributes_cols (list[str] | None): 属性列名列表。List of attribute column names

    返回 Returns
    -------
    - list[TextUnit]: 文本单元列表。List of text units
    """
    text_units = []
    for idx, row in df.iterrows():
        chunk = TextUnit(
            id=to_str(row, id_col),
            short_id=to_optional_str(row, short_id_col) if short_id_col else str(idx),
            text=to_str(row, text_col),
            entity_ids=to_optional_list(row, entities_col, item_type=str),
            relationship_ids=to_optional_list(row, relationships_col, item_type=str),
            covariate_ids=to_optional_dict(
                row, covariates_col, key_type=str, value_type=str
            ),
            text_embedding=to_optional_list(row, embedding_col, item_type=float),  # type: ignore
            n_tokens=to_optional_int(row, tokens_col),
            document_ids=to_optional_list(row, document_ids_col, item_type=str),
            attributes=(
                {col: row.get(col) for col in attributes_cols}
                if attributes_cols
                else None
            ),
        )
        text_units.append(chunk)
    return text_units


def read_documents(
    df: pd.DataFrame,
    id_col: str = "id",
    short_id_col: str = "short_id",
    title_col: str = "title",
    type_col: str = "type",
    summary_col: str | None = "entities",
    raw_content_col: str | None = "relationships",
    summary_embedding_col: str | None = "summary_embedding",
    content_embedding_col: str | None = "raw_content_embedding",
    text_units_col: str | None = "text_units",
    attributes_cols: list[str] | None = None,
) -> list[Document]:
    """
    从数据框读取文档。

    Read documents from a dataframe.

    参数 Parameters
    ----------
    - df (pd.DataFrame): 包含文档数据的数据框。Dataframe containing document data
    - id_col (str): ID 列名。ID column name
    - short_id_col (str): 短 ID 列名。Short ID column name
    - title_col (str): 标题列名。Title column name
    - type_col (str): 类型列名。Type column name
    - summary_col (str | None): 摘要列名。Summary column name
    - raw_content_col (str | None): 原始内容列名。Raw content column name
    - summary_embedding_col (str | None): 摘要嵌入列名。Summary embedding column name
    - content_embedding_col (str | None): 内容嵌入列名。Content embedding column name
    - text_units_col (str | None): 文本单元列名。Text units column name
    - attributes_cols (list[str] | None): 属性列名列表。List of attribute column names

    返回 Returns
    -------
    - list[Document]: 文档列表。List of documents
    """
    docs = []
    for idx, row in df.iterrows():
        doc = Document(
            id=to_str(row, id_col),
            short_id=to_optional_str(row, short_id_col) if short_id_col else str(idx),
            title=to_str(row, title_col),
            type=to_str(row, type_col),
            summary=to_optional_str(row, summary_col),
            raw_content=to_str(row, raw_content_col),
            summary_embedding=to_optional_list(
                row, summary_embedding_col, item_type=float
            ),
            raw_content_embedding=to_optional_list(
                row, content_embedding_col, item_type=float
            ),
            text_units=to_list(row, text_units_col, item_type=str),  # type: ignore
            attributes=(
                {col: row.get(col) for col in attributes_cols}
                if attributes_cols
                else None
            ),
        )
        docs.append(doc)
    return docs
