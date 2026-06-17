"""从文本单元集合中检索数据的工具函数。

Util functions to retrieve text units from a collection.
"""

from typing import Any, cast

import pandas as pd

from ai.components.graphrag.model import Entity, TextUnit


def get_candidate_text_units(
    selected_entities: list[Entity],
    text_units: list[TextUnit],
) -> pd.DataFrame:
    """
    获取与选定实体相关的所有文本单元。

    Get all text units that are associated to selected entities.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - text_units (list[TextUnit]): 文本单元列表。Text units list

    返回 Returns
    -------
    - pd.DataFrame: 包含文本单元数据的数据框。Dataframe containing text unit data
    """
    # 从选定实体中提取所有文本单元 ID / Extract all text unit IDs from selected entities
    selected_text_ids = [
        entity.text_unit_ids for entity in selected_entities if entity.text_unit_ids
    ]
    # 展平嵌套列表 / Flatten nested list
    selected_text_ids = [item for sublist in selected_text_ids for item in sublist]
    # 根据文本单元 ID 过滤文本单元 / Filter text units by text unit IDs
    selected_text_units = [unit for unit in text_units if unit.id in selected_text_ids]
    return to_text_unit_dataframe(selected_text_units)


def to_text_unit_dataframe(text_units: list[TextUnit]) -> pd.DataFrame:
    """
    将文本单元集合转换为 Pandas 数据框。

    Convert a list of text units to a pandas dataframe.

    参数 Parameters
    ----------
    - text_units (list[TextUnit]): 文本单元列表。Text units list

    返回 Returns
    -------
    - pd.DataFrame: 包含文本单元数据的数据框。Dataframe containing text unit data
    """
    if len(text_units) == 0:
        return pd.DataFrame()

    # 添加表头 / add header
    header = ["id", "text"]
    # 获取属性列 / Get attribute columns
    attribute_cols = (
        list(text_units[0].attributes.keys()) if text_units[0].attributes else []
    )
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    records = []
    for unit in text_units:
        new_record = [
            unit.short_id,
            unit.text,
            # 添加所有属性值 / Add all attribute values
            *[
                str(unit.attributes.get(field, ""))
                if unit.attributes and unit.attributes.get(field)
                else ""
                for field in attribute_cols
            ],
        ]
        records.append(new_record)
    return pd.DataFrame(records, columns=cast("Any", header))
