"""从实体集合中获取数据的工具函数。

Util functions to get entities from a collection.
"""

import uuid
from collections.abc import Iterable
from typing import Any, cast

import pandas as pd

from ai.components.graphrag.model import Entity


def get_entity_by_key(
    entities: Iterable[Entity], key: str, value: str | int
) -> Entity | None:
    """
    根据键获取实体。

    Get entity by key.

    参数 Parameters
    ----------
    - entities (Iterable[Entity]): 实体集合。Entities collection
    - key (str): 键名称。Key name
    - value (str | int): 键值。Key value

    返回 Returns
    -------
    - Entity | None: 匹配的实体,如果未找到则返回 None。Matched entity, or None if not found
    """
    for entity in entities:
        # 如果值是 UUID 字符串 / If value is a UUID string
        if isinstance(value, str) and is_valid_uuid(value):
            # 支持带连字符和不带连字符的 UUID 格式 / Support UUID with and without hyphens
            if getattr(entity, key) == value or getattr(entity, key) == value.replace(
                "-", ""
            ):
                return entity
        else:
            if getattr(entity, key) == value:
                return entity
    return None


def get_entity_by_name(entities: Iterable[Entity], entity_name: str) -> list[Entity]:
    """
    根据名称获取实体。

    Get entities by name.

    参数 Parameters
    ----------
    - entities (Iterable[Entity]): 实体集合。Entities collection
    - entity_name (str): 实体名称。Entity name

    返回 Returns
    -------
    - list[Entity]: 匹配的实体列表。Matched entities list
    """
    # 通过标题匹配实体 / Match entities by title
    return [entity for entity in entities if entity.title == entity_name]


def get_entity_by_attribute(
    entities: Iterable[Entity], attribute_name: str, attribute_value: Any
) -> list[Entity]:
    """
    根据属性获取实体。

    Get entities by attribute.

    参数 Parameters
    ----------
    - entities (Iterable[Entity]): 实体集合。Entities collection
    - attribute_name (str): 属性名称。Attribute name
    - attribute_value (Any): 属性值。Attribute value

    返回 Returns
    -------
    - list[Entity]: 匹配的实体列表。Matched entities list
    """
    # 过滤具有匹配属性值的实体 / Filter entities with matching attribute value
    return [
        entity
        for entity in entities
        if entity.attributes
        and entity.attributes.get(attribute_name) == attribute_value
    ]


def to_entity_dataframe(
    entities: list[Entity],
    include_entity_rank: bool = True,
    rank_description: str = "number of relationships",
) -> pd.DataFrame:
    """
    将实体集合转换为 Pandas 数据框。

    Convert a list of entities to a pandas dataframe.

    参数 Parameters
    ----------
    - entities (list[Entity]): 实体列表。Entities list
    - include_entity_rank (bool): 是否包含实体排名。Whether to include entity rank
    - rank_description (str): 排名描述。Rank description

    返回 Returns
    -------
    - pd.DataFrame: 包含实体数据的数据框。Dataframe containing entity data
    """
    if len(entities) == 0:
        return pd.DataFrame()
    # 构建表头 / Build header
    header = ["id", "entity", "description"]
    if include_entity_rank:
        header.append(rank_description)
    # 获取属性列 / Get attribute columns
    attribute_cols = (
        list(entities[0].attributes.keys()) if entities[0].attributes else []
    )
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    records = []
    for entity in entities:
        new_record = [
            entity.short_id if entity.short_id else "",
            entity.title,
            entity.description if entity.description else "",
        ]
        if include_entity_rank:
            new_record.append(str(entity.rank))

        # 添加属性值 / Add attribute values
        for field in attribute_cols:
            field_value = (
                str(entity.attributes.get(field))
                if entity.attributes and entity.attributes.get(field)
                else ""
            )
            new_record.append(field_value)
        records.append(new_record)
    return pd.DataFrame(records, columns=cast("Any", header))


def is_valid_uuid(value: str) -> bool:
    """
    判断字符串是否为有效的 UUID。

    Determine if a string is a valid UUID.

    参数 Parameters
    ----------
    - value (str): 要检查的字符串。String to check

    返回 Returns
    -------
    - bool: 如果是有效的 UUID 则返回 True,否则返回 False。True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(str(value))
    except ValueError:
        return False
    else:
        return True
