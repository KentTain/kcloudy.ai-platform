"""上下文构建实用方法。

包含为搜索系统提示词构建文本单元上下文的实用函数。

Context Build utility methods.

Contain util functions to build text unit context for the search's system prompt
"""

import random
from typing import Any, cast

import pandas as pd
import tiktoken

from ai.components.graphrag.model import Entity, Relationship, TextUnit
from ai.components.graphrag.query.llm.text_utils import num_tokens


def build_text_unit_context(
    text_units: list[TextUnit],
    token_encoder: tiktoken.Encoding | None = None,
    column_delimiter: str = "|",
    shuffle_data: bool = True,
    max_tokens: int = 8000,
    context_name: str = "Sources",
    random_state: int = 86,
) -> tuple[str, dict[str, pd.DataFrame]]:
    """
    将文本单元数据表准备为系统提示词的上下文数据。

    Prepare text-unit data table as context data for system prompt.

    参数 Parameters
    ----------
    - text_units (list[TextUnit]): 文本单元列表。List of text units
    - token_encoder (tiktoken.Encoding | None): 令牌编码器。Token encoder
    - column_delimiter (str): 列分隔符。Column delimiter
    - shuffle_data (bool): 是否打乱数据。Whether to shuffle data
    - max_tokens (int): 最大令牌数。Maximum tokens
    - context_name (str): 上下文名称。Context name
    - random_state (int): 随机种子。Random seed

    返回 Returns
    -------
    - tuple[str, dict[str, pd.DataFrame]]: 上下文文本和数据表字典。Context text and data tables dictionary
    """
    if text_units is None or len(text_units) == 0:
        return ("", {})

    # 如果需要,打乱数据
    # Shuffle data if needed
    if shuffle_data:
        random.seed(random_state)
        random.shuffle(text_units)

    # 添加上下文标题
    # add context header
    current_context_text = f"-----{context_name}-----" + "\n"

    # 添加表头
    # add header
    header = ["id", "text"]
    attribute_cols = (
        list(text_units[0].attributes.keys()) if text_units[0].attributes else []
    )
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    current_context_text += column_delimiter.join(header) + "\n"
    current_tokens = num_tokens(current_context_text, token_encoder)
    all_context_records = [header]

    # 遍历文本单元并构建上下文
    # Iterate through text units and build context
    for unit in text_units:
        new_context = [
            unit.short_id,
            unit.text,
            *[
                str(unit.attributes.get(field, "")) if unit.attributes else ""
                for field in attribute_cols
            ],
        ]
        new_context_text = column_delimiter.join(new_context) + "\n"
        new_tokens = num_tokens(new_context_text, token_encoder)

        # 检查是否超过令牌限制
        # Check if token limit is exceeded
        if current_tokens + new_tokens > max_tokens:
            break

        current_context_text += new_context_text
        all_context_records.append(new_context)
        current_tokens += new_tokens

    # 将记录转换为 DataFrame
    # Convert records to DataFrame
    if len(all_context_records) > 1:
        record_df = pd.DataFrame(
            all_context_records[1:], columns=cast("Any", all_context_records[0])
        )
    else:
        record_df = pd.DataFrame()
    return current_context_text, {context_name.lower(): record_df}


def count_relationships(
    text_unit: TextUnit, entity: Entity, relationships: dict[str, Relationship]
) -> int:
    """
    计算与文本单元相关联的所选实体的关系数量。

    Count the number of relationships of the selected entity that are associated with the text unit.

    参数 Parameters
    ----------
    - text_unit (TextUnit): 文本单元。Text unit
    - entity (Entity): 实体。Entity
    - relationships (dict[str, Relationship]): 关系字典。Relationships dictionary

    返回 Returns
    -------
    - int: 匹配的关系数量。Number of matching relationships
    """
    matching_relationships = list[Relationship]()
    # 如果文本单元没有关系 ID,则从所有关系中查找
    # If text unit has no relationship IDs, search from all relationships
    if text_unit.relationship_ids is None:
        entity_relationships = [
            rel
            for rel in relationships.values()
            if entity.title in (rel.source, rel.target)
        ]
        entity_relationships = [
            rel for rel in entity_relationships if rel.text_unit_ids
        ]
        matching_relationships = [
            rel
            for rel in entity_relationships
            if text_unit.id in rel.text_unit_ids  # type: ignore
        ]  # type: ignore
    else:
        # 从文本单元的关系 ID 中查找
        # Search from text unit's relationship IDs
        text_unit_relationships = [
            relationships[rel_id]
            for rel_id in text_unit.relationship_ids
            if rel_id in relationships
        ]
        matching_relationships = [
            rel
            for rel in text_unit_relationships
            if entity.title in (rel.source, rel.target)
        ]
    return len(matching_relationships)
