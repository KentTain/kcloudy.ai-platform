"""从关系集合中检索数据的工具函数。

Util functions to retrieve relationships from a collection.
"""

from typing import Any, cast

import pandas as pd

from ai.components.graphrag.model import Entity, Relationship


def get_in_network_relationships(
    selected_entities: list[Entity],
    relationships: list[Relationship],
    ranking_attribute: str = "rank",
) -> list[Relationship]:
    """
    获取选定实体之间的所有有向关系,按排名属性排序。

    Get all directed relationships between selected entities, sorted by ranking_attribute.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - relationships (list[Relationship]): 关系列表。Relationships list
    - ranking_attribute (str): 排名属性。Ranking attribute

    返回 Returns
    -------
    - list[Relationship]: 网络内关系列表。In-network relationships list
    """
    # 提取选定实体的标题 / Extract titles of selected entities
    selected_entity_names = [entity.title for entity in selected_entities]
    # 过滤源和目标都在选定实体中的关系 / Filter relationships where both source and target are in selected entities
    selected_relationships = [
        relationship
        for relationship in relationships
        if relationship.source in selected_entity_names
        and relationship.target in selected_entity_names
    ]
    if len(selected_relationships) <= 1:
        return selected_relationships

    # 按排名属性排序 / sort by ranking attribute
    return sort_relationships_by_ranking_attribute(
        selected_relationships, selected_entities, ranking_attribute
    )


def get_out_network_relationships(
    selected_entities: list[Entity],
    relationships: list[Relationship],
    ranking_attribute: str = "rank",
) -> list[Relationship]:
    """
    获取从选定实体到不在选定实体中的其他实体的关系,按排名属性排序。

    Get relationships from selected entities to other entities that are not within the selected entities, sorted by ranking_attribute.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - relationships (list[Relationship]): 关系列表。Relationships list
    - ranking_attribute (str): 排名属性。Ranking attribute

    返回 Returns
    -------
    - list[Relationship]: 网络外关系列表。Out-network relationships list
    """
    # 提取选定实体的标题 / Extract titles of selected entities
    selected_entity_names = [entity.title for entity in selected_entities]
    # 获取源在选定实体中但目标不在的关系 / Get relationships where source is in selected entities but target is not
    source_relationships = [
        relationship
        for relationship in relationships
        if relationship.source in selected_entity_names
        and relationship.target not in selected_entity_names
    ]
    # 获取目标在选定实体中但源不在的关系 / Get relationships where target is in selected entities but source is not
    target_relationships = [
        relationship
        for relationship in relationships
        if relationship.target in selected_entity_names
        and relationship.source not in selected_entity_names
    ]
    # 合并两类关系 / Combine both types of relationships
    selected_relationships = source_relationships + target_relationships
    return sort_relationships_by_ranking_attribute(
        selected_relationships, selected_entities, ranking_attribute
    )


def get_candidate_relationships(
    selected_entities: list[Entity],
    relationships: list[Relationship],
) -> list[Relationship]:
    """
    获取与选定实体相关的所有关系。

    Get all relationships that are associated with the selected entities.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - relationships (list[Relationship]): 关系列表。Relationships list

    返回 Returns
    -------
    - list[Relationship]: 候选关系列表。Candidate relationships list
    """
    # 提取选定实体的标题 / Extract titles of selected entities
    selected_entity_names = [entity.title for entity in selected_entities]
    # 过滤源或目标在选定实体中的所有关系 / Filter all relationships where source or target is in selected entities
    return [
        relationship
        for relationship in relationships
        if relationship.source in selected_entity_names
        or relationship.target in selected_entity_names
    ]


def get_entities_from_relationships(
    relationships: list[Relationship], entities: list[Entity]
) -> list[Entity]:
    """
    获取与选定关系相关的所有实体。

    Get all entities that are associated with the selected relationships.

    参数 Parameters
    ----------
    - relationships (list[Relationship]): 关系列表。Relationships list
    - entities (list[Entity]): 实体列表。Entities list

    返回 Returns
    -------
    - list[Entity]: 从关系中提取的实体列表。Entities extracted from relationships
    """
    # 提取所有源和目标实体名称 / Extract all source and target entity names
    selected_entity_names = [relationship.source for relationship in relationships] + [
        relationship.target for relationship in relationships
    ]
    # 过滤标题在提取的名称中的实体 / Filter entities whose titles are in extracted names
    return [entity for entity in entities if entity.title in selected_entity_names]


def calculate_relationship_combined_rank(
    relationships: list[Relationship],
    entities: list[Entity],
    ranking_attribute: str = "rank",
) -> list[Relationship]:
    """
    基于源实体和目标实体的组合排名计算关系的默认排名。

    Calculate default rank for a relationship based on the combined rank of source and target entities.

    参数 Parameters
    ----------
    - relationships (list[Relationship]): 关系列表。Relationships list
    - entities (list[Entity]): 实体列表。Entities list
    - ranking_attribute (str): 排名属性。Ranking attribute

    返回 Returns
    -------
    - list[Relationship]: 包含计算排名的关系列表。Relationships with calculated rank
    """
    # 创建实体标题到实体对象的映射 / Create mapping from entity title to entity object
    entity_mappings = {entity.title: entity for entity in entities}

    for relationship in relationships:
        if relationship.attributes is None:
            relationship.attributes = {}
        # 查找源和目标实体 / Find source and target entities
        source = entity_mappings.get(relationship.source)
        target = entity_mappings.get(relationship.target)
        # 获取源和目标实体的排名 / Get ranks of source and target entities
        source_rank = source.rank if source and source.rank else 0
        target_rank = target.rank if target and target.rank else 0
        # 计算并存储组合排名 / Calculate and store combined rank
        relationship.attributes[ranking_attribute] = source_rank + target_rank  # type: ignore
    return relationships


def sort_relationships_by_ranking_attribute(
    relationships: list[Relationship],
    entities: list[Entity],
    ranking_attribute: str = "rank",
) -> list[Relationship]:
    """
    按排名属性对关系进行排序。

    Sort relationships by a ranking_attribute.

    如果不存在排名属性,则按源实体和目标实体的组合排名排序。
    If no ranking attribute exists, sort by combined rank of source and target entities.

    参数 Parameters
    ----------
    - relationships (list[Relationship]): 关系列表。Relationships list
    - entities (list[Entity]): 实体列表。Entities list
    - ranking_attribute (str): 排名属性。Ranking attribute

    返回 Returns
    -------
    - list[Relationship]: 排序后的关系列表。Sorted relationships list
    """
    if len(relationships) == 0:
        return relationships

    # 按排名属性排序 / sort by ranking attribute
    attribute_names = (
        list(relationships[0].attributes.keys()) if relationships[0].attributes else []
    )
    if ranking_attribute in attribute_names:
        # 如果属性存在,直接按属性排序 / If attribute exists, sort directly by attribute
        relationships.sort(
            key=lambda x: int(x.attributes[ranking_attribute]) if x.attributes else 0,
            reverse=True,
        )
    elif ranking_attribute == "weight":
        # 如果排名属性是权重,按权重排序 / If ranking attribute is weight, sort by weight
        relationships.sort(key=lambda x: x.weight if x.weight else 0.0, reverse=True)
    else:
        # 排名属性不存在,计算排名 = 源实体和目标实体的组合排名
        # ranking attribute do not exist, calculate rank = combined ranks of source and target
        relationships = calculate_relationship_combined_rank(
            relationships, entities, ranking_attribute
        )
        relationships.sort(
            key=lambda x: int(x.attributes[ranking_attribute]) if x.attributes else 0,
            reverse=True,
        )
    return relationships


def to_relationship_dataframe(
    relationships: list[Relationship], include_relationship_weight: bool = True
) -> pd.DataFrame:
    """
    将关系集合转换为 Pandas 数据框。

    Convert a list of relationships to a pandas dataframe.

    参数 Parameters
    ----------
    - relationships (list[Relationship]): 关系列表。Relationships list
    - include_relationship_weight (bool): 是否包含关系权重。Whether to include relationship weight

    返回 Returns
    -------
    - pd.DataFrame: 包含关系数据的数据框。Dataframe containing relationship data
    """
    if len(relationships) == 0:
        return pd.DataFrame()

    # 构建表头 / Build header
    header = ["id", "source", "target", "description"]
    if include_relationship_weight:
        header.append("weight")
    # 获取属性列 / Get attribute columns
    attribute_cols = (
        list(relationships[0].attributes.keys()) if relationships[0].attributes else []
    )
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    records = []
    for rel in relationships:
        new_record = [
            rel.short_id if rel.short_id else "",
            rel.source,
            rel.target,
            rel.description if rel.description else "",
        ]
        if include_relationship_weight:
            new_record.append(str(rel.weight if rel.weight else ""))
        # 添加属性值 / Add attribute values
        for field in attribute_cols:
            field_value = (
                str(rel.attributes.get(field))
                if rel.attributes and rel.attributes.get(field)
                else ""
            )
            new_record.append(field_value)
        records.append(new_record)
    return pd.DataFrame(records, columns=cast("Any", header))
