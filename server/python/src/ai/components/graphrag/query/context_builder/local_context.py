"""本地上下文构建器。

Local Context Builder.
"""

from collections import defaultdict
from typing import Any, cast

import pandas as pd
import tiktoken

from ai.components.graphrag.model import Covariate, Entity, Relationship
from ai.components.graphrag.query.input.retrieval.covariates import (
    get_candidate_covariates,
    to_covariate_dataframe,
)
from ai.components.graphrag.query.input.retrieval.entities import to_entity_dataframe
from ai.components.graphrag.query.input.retrieval.relationships import (
    get_candidate_relationships,
    get_entities_from_relationships,
    get_in_network_relationships,
    get_out_network_relationships,
    to_relationship_dataframe,
)
from ai.components.graphrag.query.llm.text_utils import num_tokens


def build_entity_context(
    selected_entities: list[Entity],
    token_encoder: tiktoken.Encoding | None = None,
    max_tokens: int = 8000,
    include_entity_rank: bool = True,
    rank_description: str = "number of relationships",
    column_delimiter: str = "|",
    context_name="Entities",
) -> tuple[str, pd.DataFrame]:
    """
    将实体数据表准备为系统提示词的上下文数据。

    Prepare entity data table as context data for system prompt.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - token_encoder (tiktoken.Encoding | None): 令牌编码器。Token encoder
    - max_tokens (int): 最大令牌数。Maximum tokens
    - include_entity_rank (bool): 是否包含实体排名。Whether to include entity rank
    - rank_description (str): 排名描述。Rank description
    - column_delimiter (str): 列分隔符。Column delimiter
    - context_name (str): 上下文名称。Context name

    返回 Returns
    -------
    - tuple[str, pd.DataFrame]: 上下文文本和数据表。Context text and dataframe
    """
    if len(selected_entities) == 0:
        return "", pd.DataFrame()

    # 添加表头 / add headers
    current_context_text = f"-----{context_name}-----" + "\n"
    header = ["id", "entity", "description"]
    if include_entity_rank:
        header.append(rank_description)
    # 获取实体属性列 / Get entity attribute columns
    attribute_cols = (
        list(selected_entities[0].attributes.keys())
        if selected_entities[0].attributes
        else []
    )
    header.extend(attribute_cols)
    current_context_text += column_delimiter.join(header) + "\n"
    current_tokens = num_tokens(current_context_text, token_encoder)

    all_context_records = [header]
    for entity in selected_entities:
        new_context = [
            entity.short_id if entity.short_id else "",
            entity.title,
            entity.description if entity.description else "",
        ]
        if include_entity_rank:
            new_context.append(str(entity.rank))
        # 添加实体属性值 / Add entity attribute values
        for field in attribute_cols:
            field_value = (
                str(entity.attributes.get(field))
                if entity.attributes and entity.attributes.get(field)
                else ""
            )
            new_context.append(field_value)
        new_context_text = column_delimiter.join(new_context) + "\n"
        new_tokens = num_tokens(new_context_text, token_encoder)
        # 检查是否超过令牌限制 / Check if token limit exceeded
        if current_tokens + new_tokens > max_tokens:
            break
        current_context_text += new_context_text
        all_context_records.append(new_context)
        current_tokens += new_tokens

    if len(all_context_records) > 1:
        record_df = pd.DataFrame(
            all_context_records[1:], columns=cast("Any", all_context_records[0])
        )
    else:
        record_df = pd.DataFrame()

    return current_context_text, record_df


def build_covariates_context(
    selected_entities: list[Entity],
    covariates: list[Covariate],
    token_encoder: tiktoken.Encoding | None = None,
    max_tokens: int = 8000,
    column_delimiter: str = "|",
    context_name: str = "Covariates",
) -> tuple[str, pd.DataFrame]:
    """
    将协变量数据表准备为系统提示词的上下文数据。

    Prepare covariate data tables as context data for system prompt.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - covariates (list[Covariate]): 协变量列表。Covariates list
    - token_encoder (tiktoken.Encoding | None): 令牌编码器。Token encoder
    - max_tokens (int): 最大令牌数。Maximum tokens
    - column_delimiter (str): 列分隔符。Column delimiter
    - context_name (str): 上下文名称。Context name

    返回 Returns
    -------
    - tuple[str, pd.DataFrame]: 上下文文本和数据表。Context text and dataframe
    """
    # 创建空的协变量列表 / create an empty list of covariates
    if len(selected_entities) == 0 or len(covariates) == 0:
        return "", pd.DataFrame()

    selected_covariates = list[Covariate]()
    record_df = pd.DataFrame()

    # 添加上下文标题 / add context header
    current_context_text = f"-----{context_name}-----" + "\n"

    # 添加表头 / add header
    header = ["id", "entity"]
    attributes = covariates[0].attributes or {} if len(covariates) > 0 else {}
    attribute_cols = list(attributes.keys()) if len(covariates) > 0 else []
    header.extend(attribute_cols)
    current_context_text += column_delimiter.join(header) + "\n"
    current_tokens = num_tokens(current_context_text, token_encoder)

    all_context_records = [header]
    # 收集与选定实体相关的协变量 / Collect covariates related to selected entities
    for entity in selected_entities:
        selected_covariates.extend(
            [cov for cov in covariates if cov.subject_id == entity.title]
        )

    for covariate in selected_covariates:
        new_context = [
            covariate.short_id if covariate.short_id else "",
            covariate.subject_id,
        ]
        # 添加协变量属性值 / Add covariate attribute values
        for field in attribute_cols:
            field_value = (
                str(covariate.attributes.get(field))
                if covariate.attributes and covariate.attributes.get(field)
                else ""
            )
            new_context.append(field_value)

        new_context_text = column_delimiter.join(new_context) + "\n"
        new_tokens = num_tokens(new_context_text, token_encoder)
        # 检查是否超过令牌限制 / Check if token limit exceeded
        if current_tokens + new_tokens > max_tokens:
            break
        current_context_text += new_context_text
        all_context_records.append(new_context)
        current_tokens += new_tokens

        if len(all_context_records) > 1:
            record_df = pd.DataFrame(
                all_context_records[1:], columns=cast("Any", all_context_records[0])
            )
        else:
            record_df = pd.DataFrame()

    return current_context_text, record_df


def build_relationship_context(
    selected_entities: list[Entity],
    relationships: list[Relationship],
    token_encoder: tiktoken.Encoding | None = None,
    include_relationship_weight: bool = False,
    max_tokens: int = 8000,
    top_k_relationships: int = 10,
    relationship_ranking_attribute: str = "rank",
    column_delimiter: str = "|",
    context_name: str = "Relationships",
) -> tuple[str, pd.DataFrame]:
    """
    将关系数据表准备为系统提示词的上下文数据。

    Prepare relationship data tables as context data for system prompt.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - relationships (list[Relationship]): 关系列表。Relationships list
    - token_encoder (tiktoken.Encoding | None): 令牌编码器。Token encoder
    - include_relationship_weight (bool): 是否包含关系权重。Whether to include relationship weight
    - max_tokens (int): 最大令牌数。Maximum tokens
    - top_k_relationships (int): 每个实体的最大关系数。Maximum relationships per entity
    - relationship_ranking_attribute (str): 关系排名属性。Relationship ranking attribute
    - column_delimiter (str): 列分隔符。Column delimiter
    - context_name (str): 上下文名称。Context name

    返回 Returns
    -------
    - tuple[str, pd.DataFrame]: 上下文文本和数据表。Context text and dataframe
    """
    # 过滤和排序关系 / Filter and sort relationships
    selected_relationships = _filter_relationships(
        selected_entities=selected_entities,
        relationships=relationships,
        top_k_relationships=top_k_relationships,
        relationship_ranking_attribute=relationship_ranking_attribute,
    )

    if len(selected_entities) == 0 or len(selected_relationships) == 0:
        return "", pd.DataFrame()

    # 添加表头 / add headers
    current_context_text = f"-----{context_name}-----" + "\n"
    header = ["id", "source", "target", "description"]
    if include_relationship_weight:
        header.append("weight")
    # 获取关系属性列 / Get relationship attribute columns
    attribute_cols = (
        list(selected_relationships[0].attributes.keys())
        if selected_relationships[0].attributes
        else []
    )
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    current_context_text += column_delimiter.join(header) + "\n"
    current_tokens = num_tokens(current_context_text, token_encoder)

    all_context_records = [header]
    for rel in selected_relationships:
        new_context = [
            rel.short_id if rel.short_id else "",
            rel.source,
            rel.target,
            rel.description if rel.description else "",
        ]
        if include_relationship_weight:
            new_context.append(str(rel.weight if rel.weight else ""))
        # 添加关系属性值 / Add relationship attribute values
        for field in attribute_cols:
            field_value = (
                str(rel.attributes.get(field))
                if rel.attributes and rel.attributes.get(field)
                else ""
            )
            new_context.append(field_value)
        new_context_text = column_delimiter.join(new_context) + "\n"
        new_tokens = num_tokens(new_context_text, token_encoder)
        # 检查是否超过令牌限制 / Check if token limit exceeded
        if current_tokens + new_tokens > max_tokens:
            break
        current_context_text += new_context_text
        all_context_records.append(new_context)
        current_tokens += new_tokens

    if len(all_context_records) > 1:
        record_df = pd.DataFrame(
            all_context_records[1:], columns=cast("Any", all_context_records[0])
        )
    else:
        record_df = pd.DataFrame()

    return current_context_text, record_df


def _filter_relationships(
    selected_entities: list[Entity],
    relationships: list[Relationship],
    top_k_relationships: int = 10,
    relationship_ranking_attribute: str = "rank",
) -> list[Relationship]:
    """
    基于一组选定的实体和排名属性过滤和排序关系。

    Filter and sort relationships based on a set of selected entities and a ranking attribute.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - relationships (list[Relationship]): 关系列表。Relationships list
    - top_k_relationships (int): 每个实体的最大关系数。Maximum relationships per entity
    - relationship_ranking_attribute (str): 关系排名属性。Relationship ranking attribute

    返回 Returns
    -------
    - list[Relationship]: 过滤和排序后的关系列表。Filtered and sorted relationships list
    """
    # 第一优先级:网络内关系(即选定实体之间的关系)
    # First priority: in-network relationships (i.e. relationships between selected entities)
    in_network_relationships = get_in_network_relationships(
        selected_entities=selected_entities,
        relationships=relationships,
        ranking_attribute=relationship_ranking_attribute,
    )

    # 第二优先级 - 网络外关系(即选定实体与不在选定实体中的其他实体之间的关系)
    # Second priority -  out-of-network relationships
    # (i.e. relationships between selected entities and other entities that are not within the selected entities)
    out_network_relationships = get_out_network_relationships(
        selected_entities=selected_entities,
        relationships=relationships,
        ranking_attribute=relationship_ranking_attribute,
    )
    if len(out_network_relationships) <= 1:
        return in_network_relationships + out_network_relationships

    # 在网络外关系中,优先考虑相互关系(即与多个选定实体共享的网络外实体的关系)
    # within out-of-network relationships, prioritize mutual relationships
    # (i.e. relationships with out-network entities that are shared with multiple selected entities)
    selected_entity_names = [entity.title for entity in selected_entities]
    # 提取网络外源实体名称 / Extract out-network source entity names
    out_network_source_names = [
        relationship.source
        for relationship in out_network_relationships
        if relationship.source not in selected_entity_names
    ]
    # 提取网络外目标实体名称 / Extract out-network target entity names
    out_network_target_names = [
        relationship.target
        for relationship in out_network_relationships
        if relationship.target not in selected_entity_names
    ]
    out_network_entity_names = list(
        set(out_network_source_names + out_network_target_names)
    )
    # 计算每个网络外实体的链接数 / Calculate number of links for each out-network entity
    out_network_entity_links = defaultdict(int)
    for entity_name in out_network_entity_names:
        targets = [
            relationship.target
            for relationship in out_network_relationships
            if relationship.source == entity_name
        ]
        sources = [
            relationship.source
            for relationship in out_network_relationships
            if relationship.target == entity_name
        ]
        out_network_entity_links[entity_name] = len(set(targets + sources))

    # 按链接数和排名属性对网络外关系排序
    # sort out-network relationships by number of links and rank_attributes
    for rel in out_network_relationships:
        if rel.attributes is None:
            rel.attributes = {}
        rel.attributes["links"] = (
            out_network_entity_links[rel.source]
            if rel.source in out_network_entity_links
            else out_network_entity_links[rel.target]
        )

    # 先按 attributes[links] 排序,然后按 ranking_attribute 排序
    # sort by attributes[links] first, then by ranking_attribute
    if relationship_ranking_attribute == "weight":
        out_network_relationships.sort(
            key=lambda x: (x.attributes["links"], x.weight),  # type: ignore
            reverse=True,  # type: ignore
        )
    else:
        out_network_relationships.sort(
            key=lambda x: (
                x.attributes["links"],  # type: ignore
                x.attributes[relationship_ranking_attribute],  # type: ignore
            ),  # type: ignore
            reverse=True,
        )

    # 计算关系预算 / Calculate relationship budget
    relationship_budget = top_k_relationships * len(selected_entities)
    return in_network_relationships + out_network_relationships[:relationship_budget]


def get_candidate_context(
    selected_entities: list[Entity],
    entities: list[Entity],
    relationships: list[Relationship],
    covariates: dict[str, list[Covariate]],
    include_entity_rank: bool = True,
    entity_rank_description: str = "number of relationships",
    include_relationship_weight: bool = False,
) -> dict[str, pd.DataFrame]:
    """
    将实体,关系和协变量数据表准备为系统提示词的上下文数据。

    Prepare entity, relationship, and covariate data tables as context data for system prompt.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - entities (list[Entity]): 所有实体列表。All entities list
    - relationships (list[Relationship]): 关系列表。Relationships list
    - covariates (dict[str, list[Covariate]]): 协变量字典。Covariates dictionary
    - include_entity_rank (bool): 是否包含实体排名。Whether to include entity rank
    - entity_rank_description (str): 实体排名描述。Entity rank description
    - include_relationship_weight (bool): 是否包含关系权重。Whether to include relationship weight

    返回 Returns
    -------
    - dict[str, pd.DataFrame]: 候选上下文字典。Candidate context dictionary
    """
    candidate_context = {}
    # 获取候选关系 / Get candidate relationships
    candidate_relationships = get_candidate_relationships(
        selected_entities=selected_entities,
        relationships=relationships,
    )
    candidate_context["relationships"] = to_relationship_dataframe(
        relationships=candidate_relationships,
        include_relationship_weight=include_relationship_weight,
    )
    # 从关系中获取候选实体 / Get candidate entities from relationships
    candidate_entities = get_entities_from_relationships(
        relationships=candidate_relationships, entities=entities
    )
    candidate_context["entities"] = to_entity_dataframe(
        entities=candidate_entities,
        include_entity_rank=include_entity_rank,
        rank_description=entity_rank_description,
    )

    # 处理协变量 / Process covariates
    for covariate in covariates:
        candidate_covariates = get_candidate_covariates(
            selected_entities=selected_entities,
            covariates=covariates[covariate],
        )
        candidate_context[covariate.lower()] = to_covariate_dataframe(
            candidate_covariates
        )

    return candidate_context
